import { encodeFunctionData, type Address, type Hex } from "viem";
import { multicall3Abi, type ICall } from "./utils/contract";
import fs from 'node:fs';
import { getKmsWalletClinet, getPublicClient } from "./utils/client";
import { contractAddress } from "./utils/config";

export const sendContractCallBatch = async (calls: ICall[]): Promise<Hex> => {
  const walletClient = await getKmsWalletClinet();
  const publicClient = getPublicClient();

  const multicallCalldata = encodeFunctionData({
    abi: multicall3Abi,
    functionName: 'aggregate',
    args: [calls],
  });
  const req = await walletClient.prepareTransactionRequest({
    to: contractAddress.Multicall3 as Address,
    data: multicallCalldata,
    value: 0n,
  });

  console.log("SENDING TX")

  const serializedTrasanction = await walletClient.signTransaction(req);
  const txHash = await walletClient.sendRawTransaction({
    serializedTransaction: serializedTrasanction
  });

  await publicClient.waitForTransactionReceipt({
    hash: txHash
  });

  console.log("tx_hash", txHash);
  return txHash;
}

const calls: ICall[] = JSON.parse(fs.readFileSync('./data/all_tx.json', 'utf8'));


// sending 10 in a batch
let totalSucces = 0;
let totalAttempted = 0;

let count = 0;
let callBuffer: ICall[] = [];

console.log("Sending", calls.length)
for (const call of calls) {
  count++;
  callBuffer.push(call);
  if (count % 10 === 0) {

    totalAttempted += callBuffer.length;
    console.log(totalAttempted, totalSucces);

    try {
      const _ = await sendContractCallBatch(callBuffer);
    } catch(e) {

    }

    totalSucces += callBuffer.length;
    
    callBuffer = [];
  }
}

// send the rest of em
console.log("Sending The Remaining", callBuffer.length)
const _ = await sendContractCallBatch(callBuffer);