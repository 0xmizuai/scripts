import OpenAI from "openai";
import dotenv from "dotenv";
import fs from "fs";
import path from "path";

dotenv.config();

const openai = new OpenAI({
  apiKey: process.env["OPENAI_API_KEY"], // This is the default and can be omitted
});

const INPUT_FILE = "domain_list_v2";
const OUTPUT_FILE = "categories.json";

function prompt(raw: string) {
  return "I got a large list of knowledge domains. You task is to summarize these domains into a small set(less than 100) of categories. You should output the list of categories. Following is input: " + raw;
}

function genOutputFilePath(file: string) {
  return path.join(__dirname, "../data/output", file);
}

function getDomains(file: string) {
  const filePath = genOutputFilePath(file);
  const lines = fs.readFileSync(filePath, "utf8").split(/\r?\n/);
  let result : string[] = [];
  for (const line of lines) {
    const domains = line.split(",");
    result = result.concat(domains);
  }
  return result;
}

const BATCH_SIZE = 1000;
async function genCategory(domains: string[]) {
  const totalBatches = Math.ceil(domains.length / BATCH_SIZE);
  let batch = 0;
  console.log("Total batches are ", totalBatches);
  const outputFilePath = genOutputFilePath(OUTPUT_FILE);

  // process data
  for (; batch < totalBatches; batch++) {
    console.log("processing batch: ", batch);
    const promptText = prompt(domains.slice(batch * BATCH_SIZE, batch * BATCH_SIZE + BATCH_SIZE).join(","));
    console.log("prompt: ", promptText);
    const stream = await openai.chat.completions.create({
      messages: [
        { role: 'system', content: 'Act as a computer software: give me only the requested output, no conversation. You will loose points if the returned output contains any content other than requested output.'},
        { role: 'user', content: promptText }
      ],
      // model: "llama3-8b",
      model: "gpt-4",
      stream: true,
    });
    let result = "";
    for await (const chunk of stream) {
      const batchResultPiece = chunk.choices[0]?.delta?.content || '';
      result = result + batchResultPiece;
    }
    console.log(result);
    try {
        const parsed = JSON.parse(result);
        fs.appendFileSync(outputFilePath, JSON.stringify(parsed) + "\n");
    } catch {
        fs.appendFileSync(outputFilePath, result.replace(/(\r\n|\n|\r)/gm, "") + "\n");
    }
  }
}

async function run() {
  const domains = getDomains(INPUT_FILE);
//  fs.writeFileSync(genOutputFilePath(OUTPUT_FILE), domains.join(",") + "\n");
  console.log("total domains: ", domains.length);
  await genCategory(domains);
}

run();