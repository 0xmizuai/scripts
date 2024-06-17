import { MongoClient, Db, Collection, Timestamp } from 'mongodb';
import crypto from 'crypto';
import dotenv from 'dotenv';

dotenv.config();
// MongoDB connection URI
const uri = process.env['MONGODB_URI'];
if (!uri) {
    throw new Error("The environment variable MONGODB_URI is required.")
}
const client = new MongoClient(uri);

interface InferenceCache {
    _id: string;
    input: string;
    output: string;
    prompt_id: string;
    model: string;
    service: string;
    inferred_at: number;
    created_at: number;
}

interface Prompt {
    _id: string;
    content: string;
    created_at: number;
}

let db: Db;
let inferenceCacheCollection: Collection<InferenceCache>;
let promptCollection: Collection<Prompt>;

async function initializeDb() {
    await client.connect();
    db = client.db(process.env['MONGODB_DB']);
    
    inferenceCacheCollection = db.collection<InferenceCache>('inference_cache');
    promptCollection = db.collection<Prompt>('prompt');

    await db.createCollection('inference_cache').catch((e) => {
        if (e.codeName !== 'NamespaceExists') throw e;
    });
    
    await db.createCollection('prompt').catch((e) => {
        if (e.codeName !== 'NamespaceExists') throw e;
    });
}

function sha256(data: string): string {
    return crypto.createHash('sha256').update(data).digest('hex');
}

async function checkAndCache(input: string, output: string, promptContent: string, service: string, model: string): Promise<boolean> {
    const promptId = sha256(promptContent);
    const _id = sha256(`${input}_${promptId}_${service}_${model}`);
    const existingPrompt = await promptCollection.findOne({ _id: promptId });
    const currentTimestamp = Math.floor(Date.now() / 1000);
    if (!existingPrompt) {
        await promptCollection.insertOne({
            _id: promptId,
            content: promptContent,
            created_at: currentTimestamp,
        });
    }

    const result = await inferenceCacheCollection.findOne({ _id });
    if (result) {
        return true;
    } else {
        await inferenceCacheCollection.insertOne({
            _id,
            input,
            output,
            prompt_id: promptId,
            model,
            service,
            inferred_at: currentTimestamp,
            created_at: currentTimestamp,
        });
        return false;
    }
}

// Example call
(async () => {
    await initializeDb();
    
    const input = 'raw data example';
    const output = 'clean data example';
    const promptContent = 'example prompt content';
    const service: 'lepton' | 'zillion' = 'lepton';
    const model = 'llama3';
    
    const cacheExists = await checkAndCache(input, output, promptContent, service, model);
    console.log(`Cache exists: ${cacheExists}`);
    
    await client.close();
})();
