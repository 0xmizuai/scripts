import { MongoClient, ObjectId } from 'mongodb';
import fs from 'fs';
import path from 'path';
import dotenv from 'dotenv';
import crypto from 'crypto'

dotenv.config();
function sha256(data: string): string {
  return crypto.createHash('sha256').update(data).digest('hex');
}

// MongoDB connection URI
const uri = process.env['MONGODB_URI'];
if (!uri) {
    throw new Error("The environment variable MONGODB_URI is required.");
}
const client = new MongoClient(uri);

// Define the RepoMetadata structure
interface RepoMetadata {
    _id: string;
    address: string;
    title: string;
    description: string;
    category: string;
    validation_rules: string[];
}

// Read domains from the domain_list_36680 file
function readDomains(filePath: string): string[] {
    const fileContent = fs.readFileSync(filePath, 'utf8');
    return fileContent.split(',').map(domain => domain.trim());
}

async function main() {
    try {
        await client.connect();
        const database = client.db(process.env.MONGODB_DB);
        const collection = database.collection<RepoMetadata>('repo_metadata');
        if (!process.env.MONGODB_DATA_REPO) {
          throw new Error("data repo collection should be there.");
        }
          
        const repoCollection = database.collection(process.env.MONGODB_DATA_REPO);

        // Read the domain list
        const domains = readDomains(path.join(__dirname, '..', 'data', 'categories_1444'));

        // Read addresses from repo_chain_interfaces collection
        const addressesCursor = repoCollection.find({}, { projection: { address: 1 } });
        const addresses = await addressesCursor.toArray();

        // Ensure we have enough addresses
        if (addresses.length < domains.length) {
            throw new Error("Not enough addresses in the repo_chain_interfaces collection.");
        }

        // Create and insert metadata for each domain
      const metadataList: RepoMetadata[] = domains.map((domain, index) => {
        const title = `dolma_shard_${index + 1}`;
        const description = `This is the sub-dataset generated from dolma for category ${domain}.`;
        const _id = sha256(`${title}_${description}`);

        return {
            _id, // Use the generated hash value as _id
            address: addresses[index].address, // Assign address from repo_chain_interfaces
            title,
            description,
            category: domain,
            validation_rules: []
        };
        });

        await collection.insertMany(metadataList);
        console.log('Metadata inserted successfully.');
    } catch (error) {
        console.error('An error occurred:', error);
    } finally {
        await client.close();
    }
}

main().catch(console.error);
