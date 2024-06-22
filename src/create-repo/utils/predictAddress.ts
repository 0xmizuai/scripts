import type {Address, Hex} from 'viem';
import { encodeFunctionData, keccak256, toBytes, toHex } from "viem";
import { contractFactoryAbi } from './contract';
import { getPublicClient } from './client';
import { contractAddress } from './config';


export const toAddress = (bytes: Hex) => {
  const b = toBytes(bytes);
  return toHex(b.slice(12));
};

export const makeSalt = (initData: Hex): Hex => {
  const tag = keccak256(toBytes('dolma_dataset_v1_277'));
  const salt = keccak256(`${initData}${tag.substring(2)}`);
  return salt;
}

export const predictAddress = async ( initData: Hex ) => {
  const salt = makeSalt(initData);
  const predictAddressCalldata = encodeFunctionData({
    abi: contractFactoryAbi,
    functionName: 'predictClonedAddress',
    args: [salt],
  });

  let publicClient = getPublicClient();
  const repoAddressData = await publicClient.call({
    to: contractAddress.ContractFactory as Address,
    data: predictAddressCalldata,
  });
  const repoAddress = toAddress(repoAddressData.data as Hex);
  console.log("repoAddress", repoAddress);

  return repoAddress;
}
  