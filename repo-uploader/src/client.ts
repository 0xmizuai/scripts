import { Address, createPublicClient, createWalletClient, http, keccak256, parseSignature, serializeTransaction, toBytes, toHex } from "viem";
import { mnemonicToAccount, privateKeyToAccount, signTransaction, toAccount } from "viem/accounts";
import { holesky } from "viem/chains";
import { serverHosts } from "./host";
import superagent from "superagent";


export function getPublicClient() {
  const rpc = process.env.RPC_URL as string;
  const publicClient = createPublicClient({
    chain: holesky,
    transport: http(rpc),
  });

  return publicClient;
}

export function getTestAccountAddress() {
  const testSeed = process.env.TEST_SEED as string;
  const testPrivateKey = process.env.TEST_PRIVATE_KEY as `0x${string}`;

  const account = testSeed
    ? mnemonicToAccount(process.env.TEST_SEED as string)
    : privateKeyToAccount(testPrivateKey);

  return account.address;
}

export async function getKmsWalletClinet() {
  const rpc = process.env.INFURA_RPC_URL;
  const ownerAddress = process.env.DATA_REPO_OWNER;

  const account = toAccount({
    address: ownerAddress as Address,
    async signMessage({ message }) {
      console.log("ERROR")

      return '0x00'
    },
    async signTransaction(transaction) {
      const serializedTransaction = serializeTransaction(transaction);
      const txHash = keccak256(serializedTransaction);
      const sig = await superagent
        .post(`${serverHosts.signer}/admin/sign_hash`)
        .send({
          data: txHash.substring(2),
        })
        .then(
          (res) => JSON.parse(res.body.data).result
        );

      return serializeTransaction(transaction, parseSignature(`0x${sig as string}`));
    },
    async signTypedData(typedData) {
      console.log("ERROR")
      return '0x00'
    },
  });

  const walletClient = createWalletClient({
    account,
    chain: holesky,
    transport: http(rpc),
  });

  return walletClient;
}
