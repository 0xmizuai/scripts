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

export const createNewRepo = async () => {
  // const stringified = JSON.stringify({ title, description, validationRules: validationRule });
  // const metadataHash = keccak256(toBytes(stringified));

  const walletClient = await getKmsWalletClinet();
  const publicClient = getPublicClient();

  let metadata: `0x${string}` = `0x${'0'.repeat(64)}`;
  console.log('Generated metadataHash:', metadata);
  
  const initData = calldataInitData(
    process.env.DATA_REPO_OWNER as Address,
    metadata,
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

  console.log("Balance: " + await publicClient.getBalance({
    address: process.env.DATA_REPO_OWNER as Address,
  }))

  const serializedTrasanction = await walletClient.signTransaction(req);
  const txHash = await walletClient.sendRawTransaction({
    serializedTransaction: serializedTrasanction
  });

  console.log("tx_hash", txHash);
  return txHash;
};

export const toAddress = (bytes: Hex) => {
  const b = toBytes(bytes);
  return toHex(b.slice(12));
};
