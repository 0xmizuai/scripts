import superagent from 'superagent';
import { config } from '../config';
import { ethers } from 'ethers';

export const signData = async (data: string) => {
  const hash = ethers.getBytes(data);
  const hexHash = ethers.hexlify(hash).replace(/^0x/, ''); // Remove '0x' prefix for API compatibility

  try {
    const response = await superagent
      .post(config.kmsApi)
      .send({ data: hexHash });

      if (!response.body.data) {
        throw new Error('No data in response');
      }
  
      const result = JSON.parse(response.body.data);
      const signature = result.result;
      if (!signature) {
        throw new Error('Signature is undefined');
      }

    // Convert the signature to a Buffer
    const signatureBuffer = Buffer.from(signature, 'hex');

    const splitSignature = ethers.Signature.from({
      r: '0x' + signatureBuffer.slice(0, 32).toString('hex'),
      s: '0x' + signatureBuffer.slice(32, 64).toString('hex'),
      v: signatureBuffer[64] + 27,
    });

    return splitSignature.serialized;
  } catch (error) {
    console.error('Error signing data with KMS API:', error);
    throw new Error('Failed to sign data');
  }
};
