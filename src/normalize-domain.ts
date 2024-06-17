import OpenAI from 'openai';
import dotenv from 'dotenv';
import fs from 'fs';
import path from 'path';

dotenv.config();

const openai = new OpenAI({
  apiKey: process.env['OPENAI_API_KEY'], // This is the default and can be omitted
});

const INPUT_FILE = "test_for_backend.stats_kdomain-v.762k.json";
const OUTPUT_FILE = "normalized_domains.json";

function prompt(raw: string) {
  return "I got a list of knowledge domains but they are not normalized. You task is to normalize all these domains. You should output and only output the json where the key is the raw data and the value is an array of normalized strings in snake case. You should process all data listed. Following is the list separated by '_': " + raw;
}

function genInputFilePath(file: string) {
  return path.join(__dirname, "../data", file);
}

function genOutputFilePath(file: string) {
  return path.join(__dirname, "../data/output", file);
}

function getDomains(file: string): string[] {
  const filePath = genInputFilePath(file);
  console.log("Loading domains from: ", filePath);
  const domains = JSON.parse(fs.readFileSync(filePath, 'utf8'));
  return (domains[0] as {data: [{_id: string}]}).data.map(d => d._id);
}

async function run() {
  const domains = getDomains(INPUT_FILE);
  const totalBatches = Math.ceil(domains.length / 100);
  const outputFile = genOutputFilePath(OUTPUT_FILE);
  console.log("Will output normailized domains to file ", outputFile);
  console.log("Total batches are ", totalBatches);

  // read checkpoint
  const progressFile = genOutputFilePath('.' + INPUT_FILE + '.progress');
  let progress: {batch: number} = {batch: -1};
  if (fs.existsSync(progressFile)) {
    progress = JSON.parse(fs.readFileSync(progressFile, 'utf8'));
  }
  let batch = progress.batch + 1;

  // process data
  for (; batch < totalBatches; batch++) {
    console.log("Processing batch ", batch);
    const selected = domains.slice(batch * 100, (batch + 1) * 100);
    if (selected.length == 0) {
      console.log("No more domains to process");
      return;
    }

    const promptText = prompt(selected.join("_").replace(/(\r\n|\n|\r)/gm, ""));
    console.log(promptText);
    const stream = await openai.chat.completions.create({
      messages: [
        { role: 'system', content: 'Act as a computer software: give me only the requested output, no conversation. You will loose points if the returned output contains any content other than requested output.'},
        { role: 'user', content: promptText }
      ],
      model: 'gpt-4',
      stream: true,
    });
    for await (const chunk of stream) {
      const result = chunk.choices[0]?.delta?.content || '';
      process.stdout.write(result);
      fs.appendFile(outputFile, result, function (err) {
        if (err) throw err;
      });
    }

    // record checkpoint
    progress.batch = batch;
    fs.writeFileSync(outputFile, JSON.stringify(progress));
  }
}

run();
