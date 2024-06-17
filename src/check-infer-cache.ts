import { MongoClient, Db, Collection } from 'mongodb';
import crypto from 'crypto';

// MongoDB connection URI
const uri = 'mongodb://mongo:AQxXJzLKsipZQAfRwaaAHwhoUUByeNWn@viaduct.proxy.rlwy.net:37789';
const client = new MongoClient(uri);

interface InferenceCache {
    _id: string;
    input: string;
    output: string;
    prompt_id: string;
    model: string;
    service: string;
    inferred_at: Date;
    created_at: Date;
}

interface Prompt {
    _id: string;
    content: string;
    created_at: Date;
}

let db: Db;
let inferenceCacheCollection: Collection<InferenceCache>;
let promptCollection: Collection<Prompt>;

async function initializeDb() {
    await client.connect();
    db = client.db('test');
    
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
    if (!existingPrompt) {
        await promptCollection.insertOne({
            _id: promptId,
            content: promptContent,
            created_at: new Date(),
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
            inferred_at: new Date(),
            created_at: new Date(),
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
