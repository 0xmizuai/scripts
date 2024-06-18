import { ethers } from 'ethers';
import { signData } from './utils/kms';
import { config } from './config';
import { contractAddress } from './address';

const provider = new ethers.JsonRpcProvider(config.infuraRpcUrl);

const main = async () => {
  const network = await provider.getNetwork();
  const chainId = network.chainId;

  const to = contractAddress.ContractFactory; 
  const value = ethers.parseEther('0.01'); // Sending 0.01 ETH

  const unsignedTx = {
    to,
    value,
    gasLimit: ethers.toBeHex(21000), // Basic transaction gas limit
    chainId,
  };

  // Create transaction from unsigned transaction
  const tx = ethers.Transaction.from(unsignedTx);

  // Hash the transaction to get the digest to sign
  const txHashToSign = tx.unsignedHash;

  // Sign the transaction digest
  const signature = await signData(txHashToSign);

  // Apply the signature to the transaction
  tx.signature = signature;

  // Serialize the transaction with the signature
  const signedTx = tx.serialized;


  // Get the from address from the signature
  const fromAddress = ethers.recoverAddress(txHashToSign, signature);
  const balance = await provider.getBalance(fromAddress);
  console.log(`Balance of ${fromAddress}: ${ethers.formatEther(balance)} ETH`);

  const txResponse = await provider.broadcastTransaction(signedTx);
  return txResponse.hash;
};

main().catch(console.error);
