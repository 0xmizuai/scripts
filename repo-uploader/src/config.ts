import dotenv from 'dotenv';

dotenv.config();

export const config = {
  dataRepoOwner: process.env.DATA_REPO_OWNER!,
  kmsApi: process.env.KMS_API!,
  kmsKeyId: process.env.MIZU_REPO_OWNER_KEY!,
  infuraRpcUrl: process.env.INFURA_RPC_URL!,
};
