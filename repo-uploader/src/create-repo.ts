import { keccak256, toBytes, toHex, type Address, type Hex } from 'viem';
import { contractAddress } from './address';
import { getKmsWalletClinet, getPublicClient, getTestAccountAddress } from './client';
import {
  calldataClone,
  calldataInitData,
  calldataPredictAddress,
} from './contract';
import dotenv from 'dotenv';

dotenv.config();

export const createNewRepo = async (title: string, description: string, validationRule: string[]) => {
  // const stringified = JSON.stringify({ title, description, validationRules: validationRule });
  // const metadataHash = keccak256(toBytes(stringified));

  const walletClient = await getKmsWalletClinet();
  const publicClient = getPublicClient();

  const timestamp = Math.floor(Date.now() / 1000);
  const timestampHex = timestamp.toString(16).padStart(16, '0');
  let metadataHash: `0x${string}` = `0x${'0'.repeat(48)}${timestampHex}`;
  console.log('Generated metadataHash:', metadataHash);
  
  const initData = calldataInitData(
    process.env.DATA_REPO_OWNER as Address,
    metadataHash,
    contractAddress.MizuPoints as Address,
    1000n
  );
  const cloneCalldata = calldataClone(initData);
  const predictAddressCalldata = calldataPredictAddress(initData);

  const repoAddressData = await publicClient.call({
    to: contractAddress.ContractFactory as Address,
    data: predictAddressCalldata,
  });
  const repoAddress = toAddress(repoAddressData.data as Hex);
  console.log({ repoAddress });

  const req = await walletClient.prepareTransactionRequest({
    to: contractAddress.ContractFactory as Address,
    data: cloneCalldata,
    value: 0n,
  });

  console.log("SENDING TX")

  console.log(await publicClient.getBalance({
    address: process.env.DATA_REPO_OWNER as Address,
  }))

  const serializedTrasanction = await walletClient.signTransaction(req);
  const txHash = await walletClient.sendRawTransaction({
    serializedTransaction: serializedTrasanction
  });

  console.log(repoAddress);
  console.log("tx_hash", txHash);

  return txHash;
};

export const toAddress = (bytes: Hex) => {
  const b = toBytes(bytes);
  return toHex(b.slice(12));
};
