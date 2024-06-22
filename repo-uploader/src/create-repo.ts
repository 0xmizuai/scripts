import { keccak256, PublicClient, toBytes, toHex, type Address, type Hex } from 'viem';
import { contractAddress } from './address';
import { getKmsWalletClinet, getPublicClient, getTestAccountAddress } from './client';
import {
  calldataClone,
  calldataInitData,
  calldataMulticall,
  calldataPredictAddress,
  ICall,
} from './contract';

export const createEmptyNewRepo = async (offset: number) => {
  const walletClient = await getKmsWalletClinet();
  const publicClient = getPublicClient();

  let allCalls: ICall[] = []
  for (let i = 0; i < 10; i ++) {
    const metadataHash = generateMetadata(i + offset);
    const initData = calldataInitData(
      "0x0069f8e371b71f7996523c22bae7ea221666f06c" as Address,
      metadataHash,
      contractAddress.MizuPoints as Address,
      0n
    );
    const cloneCalldata = calldataClone(initData);
    allCalls.push({ target: contractAddress.ContractFactory as Address, callData: cloneCalldata })
  }


  const multiCallData = calldataMulticall(allCalls);
  const req = await walletClient.prepareTransactionRequest({
    to: contractAddress.Multicall3 as Address,
    data: multiCallData,
    value: 0n,
  });

  console.log("SENDING TX")
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


export const predictAddress = async (
  publicClient: PublicClient,
  initData: Hex,
) => {
  const predictAddressCalldata = calldataPredictAddress(initData);

  const repoAddressData = await publicClient.call({
    to: contractAddress.ContractFactory as Address,
    data: predictAddressCalldata,
  });
  const repoAddress = toAddress(repoAddressData.data as Hex);
  console.log({ repoAddress });
}

export const generateMetadata = (source: number): Hex => {
  const sourceHex = source.toString(16).padStart(16, '0');
  let metadataHash: `0x${string}` = `0x${'0'.repeat(48)}${sourceHex}`;
  return metadataHash;
}