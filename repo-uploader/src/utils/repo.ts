import { ethers, getBytes, Interface, keccak256, toUtf8Bytes  } from 'ethers';
import { signData } from './kms';
import { config } from '../config';
import { contractAddress } from '../address';

function calldataInitData(ownerAddress: string, metadataHash: string, tokenAddress: string, price: bigint): string {
  const iface = new Interface([
    "function initialize(address owner, bytes32 metadataHash, address token, uint256 price)"
  ]);

  return iface.encodeFunctionData("initialize", [ownerAddress, metadataHash, tokenAddress, price]);
}

export const createNewRepo = async (title: string, description: string, validationRule: string[]) => {
  const stringified = JSON.stringify({ title, description, validationRules: validationRule });
  const metadataHash = keccak256(ethers.toUtf8Bytes(stringified));

  // Sign the metadata hash using KMS
  const signedData = await signData(metadataHash);

  // Recover the address from the signed metadata hash
  const recoveredAddress = ethers.recoverAddress(metadataHash, signedData);
  console.log(`Recovered Address from Metadata Hash: ${recoveredAddress}`);

  const provider = new ethers.JsonRpcProvider(config.infuraRpcUrl);
  const balance = await provider.getBalance(recoveredAddress);
  console.log(`Balance of ${recoveredAddress}: ${ethers.formatEther(balance)} ETH`);

  // if (balance <= 0) {
  //   throw new Error('Insufficient funds in the account');
  // }

  const initData = calldataInitData(
    config.dataRepoOwner,  
    metadataHash,
    contractAddress.MizuPoints,
    1000n
  );

  const iface = new Interface([
    "function clone(bytes32 salt, bytes memory initData, bytes memory signature)"
  ]);
  const salt = keccak256(initData);
  const cloneCalldata = iface.encodeFunctionData("clone", [salt, initData, signedData]);

  const network = await provider.getNetwork();
  const chainId = network.chainId;

  // Create the transaction object
  const unsignedTx = {
    to: contractAddress.ContractFactory,
    data: cloneCalldata,
    gasLimit: ethers.toBeHex(2000000),
    chainId,
  };

  // Serialize the unsigned transaction
  const tx = ethers.Transaction.from(unsignedTx);
  const txHashToSign = tx.unsignedHash;

  // Sign the transaction hash using KMS
  const signature = await signData(txHashToSign);

  // Apply the signature to the transaction
  tx.signature = signature;

  // Serialize the signed transaction
  const signedTx = tx.serialized;

  // Send the transaction
  const txResponse = await provider.broadcastTransaction(signedTx);

  console.log('Transaction hash:', txResponse.hash);

  const txReceipt = await provider.getTransactionReceipt(txResponse.hash);
  if (txReceipt) {
    console.log(`Transaction ${txResponse.hash} mined in block ${txReceipt.blockNumber}`);
  } else {
    console.log(`Transaction ${txResponse.hash} not yet mined`);
  }

  return txResponse.hash;
};
