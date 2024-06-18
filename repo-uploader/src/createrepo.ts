import { keccak256, toBytes, toHex, type Address, type Hex, getAddress } from 'viem';
import { contractAddress } from './address';
import { getKmsWalletClinet, getPublicClient, getTestAccountAddress } from './client';
import {
  calldataClone,
  calldataInitData,
  calldataPredictAddress,
} from './contract';

export const createNewRepo = async (title: string, description: string, validationRule: string[]) => {
  const stringified = JSON.stringify({ title, description, validationRules: validationRule });
  const metadataHash = keccak256(toBytes(stringified));

  const walletClient = await getKmsWalletClinet();
  const publicClient = getPublicClient();

  const initData = calldataInitData(
    getTestAccountAddress(),
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
    address: "0x0069f8e371b71f7996523c22bae7ea221666f06c",
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
