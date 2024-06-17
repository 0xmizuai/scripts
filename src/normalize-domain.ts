import OpenAI from 'openai';
import dotenv from 'dotenv';
import fs from 'fs';
import path from 'path';

dotenv.config();
const openai = new OpenAI({
  apiKey: process.env['OPENAI_API_KEY'], // This is the default and can be omitted
});

function prompt(raw: string) {
  return "Act as a computer software: give me only the requested output, no conversation. You'll loose points if the returned output contains any content other than requested output. I got a list of knowledge domains but they are not normalized. You task is to normalize all these domains. You should output and only output the json where the key is the raw data and the value is an array of normalized strings in snake case. You should process all data listed and if you cannot process them all, notify me at the end of the conversation and list number of records you processed in this round. Following is the list separated by '_': " + raw;
}

function getDomains(file: string): string[] {
  const filePath = path.join(__dirname, "../data", file);
  console.log("Loading domains from: ", filePath);
  const domains = JSON.parse(fs.readFileSync(filePath, 'utf8'));
  return (domains[0] as {data: [{_id: string}]}).data.map(d => d._id);
}

async function run() {
  const domains = getDomains("../data/" + "test_for_backend.stats_kdomain-v.762k.json");
  console.log("Domains samples are: ", domains.slice(0, 500));
  const promptText = prompt(domains.slice(0, 500).join("_").replace(/(\r\n|\n|\r)/gm, ""));
  console.log("Prompt text is: ", promptText);
  const stream = await openai.chat.completions.create({
    messages: [{ role: 'user', content: promptText }],
    model: 'gpt-4',
    stream: true,
  });
  for await (const chunk of stream) {
    process.stdout.write(chunk.choices[0]?.delta?.content || '');
  }
}

run();
