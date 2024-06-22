import superagent from "superagent";
import { serverHosts } from "./utils/config";
import { getPublicClient } from "./utils/client";
import { encodeAbiParameters, encodeFunctionData, keccak256, parseAbiParameters, parseUnits, toFunctionSelector, type Address, type Hex } from "viem";
import { dataRepoAbi, type ICall } from "./utils/contract";

const getNonce = async(repo: Address): Promise<bigint> => {
  const publicClient = getPublicClient();
  const result = await publicClient.call({
    to: repo,
    data: encodeFunctionData({
      abi: dataRepoAbi,
      functionName: "getNonce",
      args: [],
    }),
  });
  return parseUnits(result.data as Hex, 1);
}

const getPayload = async(repo: Address, commit: string, amount: number): Promise<ICall> => {
  const publicClient = getPublicClient();
  const chainId = BigInt(await publicClient.getChainId());
  const nonce = await getNonce(repo);
  const selector = toFunctionSelector(dataRepoAbi[9]);

  const encodedPayload = keccak256(
    encodeAbiParameters(
      parseAbiParameters(
        "uint chainId, address deployedAddr, bytes4 selector, uint256 nonce, address owner, bytes32 commitment, uint256 size"
      ),
      [chainId, repo, selector, nonce, "0x0069f8e371B71F7996523c22BAe7eA221666f06C", `0x${commit}`, BigInt(amount)]
    )
  );

  const s2 = await superagent.post(`${serverHosts.signer}/sign_hash`).send({
    data: encodedPayload.substring(2), // stripe 0x
  });

  const signature = JSON.parse(s2.body.data).result;
  const calldata = encodeFunctionData({
    abi: dataRepoAbi,
    functionName: "commit",
    args: [
      "0x0069f8e371B71F7996523c22BAe7eA221666f06C",
      `0x${commit}`,
      BigInt(amount),
      `0x${signature}`,
    ],
  })

  return {
    target: repo,
    callData: calldata
  };
}

const result = await superagent
  .get(`${serverHosts.da}/dump`);

const pending = JSON.parse(result.text)["data"]["pending_commits"];

let callBuff: ICall[] = [];
for (const commit of pending) {
  const result = await superagent
    .get(`${serverHosts.da}/read/commit_by_hash/${commit}`);
  
  const comm = JSON.parse(result.text)["data"]["commits"][0];
  console.log(comm.repo, comm._id, comm.importingAmount)
  // const call = await getPayload(comm.repo, comm._id, comm.importingAmount);
  // callBuff.push(call)
}

console.log(JSON.stringify(callBuff))