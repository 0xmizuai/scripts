
import { encodeFunctionData, keccak256, toBytes, type Address, type Hex } from 'viem';
import { getKmsWalletClinet, getPublicClient } from './client';
import { calldataSetMetadata, dataRepoAbi } from './contract';
import dotenv from 'dotenv';
import { toAddress } from './create-repo';

dotenv.config();

export const setMetadata = async (repoAddress: Address, newMetadata: string) => {
  const walletClient = await getKmsWalletClinet();
  const publicClient = getPublicClient();
  const metadataHash = keccak256(toBytes(newMetadata));

  const setMetadataData = calldataSetMetadata(
    metadataHash,
  );

  const ownerAddress = await publicClient.call({
    to: repoAddress,
    data: encodeFunctionData({
      abi: dataRepoAbi,
      functionName: 'getOwner',
    }),
  });
  
  console.log('Owner Address:', toAddress(ownerAddress.data as Hex));
  
  const req = await walletClient.prepareTransactionRequest({
    to: repoAddress,
    data: setMetadataData,
    value: 0n,
  });

  const serializedTransaction = await walletClient.signTransaction(req);
  const txHash = await walletClient.sendRawTransaction({
    serializedTransaction,
  });

  console.log('tx_hash', txHash);

  return txHash;
};