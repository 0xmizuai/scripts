import OpenAI from 'openai';
import dotenv from 'dotenv';
import fs from 'fs';
import path from 'path';

dotenv.config();

const openai = new OpenAI({
  apiKey: process.env['LEPTON_API_KEY'], // This is the default and can be omitted
  baseURL: "https://llama3-8b.lepton.run/api/v1",
}); 

// const openai = new OpenAI({
//   apiKey: "NONE", // This is the default and can be omitted
//   baseURL: "http://209.170.83.61:7860/v1",
// });

const INPUT_FILE = "test_for_backend.stats_kdomain-v.762k.json";
const OUTPUT_FILE = "normalized_domains_v2.json";
const SEPARATOR = "______";

function prompt(raw: string) {
  return "I got a list of knowledge domains but they are not normalized. You task is to normalize all these domains. You should strip all conversational text such as 'here is the output' and 'the knowledge domain is...'. The input may contains multiple domains separated by backslash or 'and', you should split them into an array per the semantic. You should output and only output the json where the key is the raw data and the value is an array of normalized domains in snake case. You should process all data listed. Following is the list of domains separated by " + SEPARATOR + ": " + raw;
}

function prompt2(raw: string) {
  return `Given the knowledge domain description ${raw}, please normalize the input into a list of domains. ###Things to consider when generating the knowledge domains###  - All conversational text such as 'here is the output' and 'the knowledge domain is...' should be stripped. - The input may contain multiple domains separated by '/' or 'and', you should split them into array of domains properly per its semantic. - The output has to be an array of normalized domains separated by comma. - Each normalized domain should be with snake case.`;
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

  // read checkpoint
  const progressFile = genOutputFilePath('.' + INPUT_FILE + '.progress');
  let progress: {batch: number} = {batch: -1};
  if (fs.existsSync(progressFile)) {
    progress = JSON.parse(fs.readFileSync(progressFile, 'utf8'));
  }
  let i = progress.batch + 1;

  // read output file
  const outputFilePath = genOutputFilePath(OUTPUT_FILE);
  console.log("Will output normailized domains to file ", outputFilePath);

  // const totalBatches = Math.ceil(domains.length / 10);
  // console.log("Total batches are ", totalBatches);
  // process data
  for (; i < domains.length; i++) {
    console.log("Processing ", i);
    const promptText = prompt2(domains[i].replace(/(\r\n|\n|\r)/gm, ""));
    const stream = await openai.chat.completions.create({
      messages: [
        { role: 'system', content: 'Act as a computer software: give me only the requested output, no conversation. You will loose points if the returned output contains any content other than requested output.'},
        { role: 'user', content: promptText }
      ],
      // model: "llama3-8b",
      model: "Llama-3-8B-Instruct",
      stream: true,
    });
    let result = "";
    for await (const chunk of stream) {
      const batchResultPiece = chunk.choices[0]?.delta?.content || '';
      result = result + batchResultPiece;
    }
    fs.appendFileSync(outputFilePath, result + "\n");
    console.log("domain: ", result);

    // record checkpoint
    progress.batch = i;
    fs.writeFileSync(progressFile, JSON.stringify(progress));
  }
}

run();
