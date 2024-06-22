import {
  encodeFunctionData,
  keccak256,
  parseAbi,
  type Address,
  type Hex,
} from "viem";
import { contractAddress } from "./address";

export const dataRepoAbi = parseAbi([
  "function initialize(address _owner, bytes memory _metadata, address _token, uint256 _price) public",
  "function getValidator() public view returns (address)",

  "function setOwner(address newOwner) public",
  "function getOwner() public view returns (address)",

  "function getMetadata() external view returns (bytes memory)",
  "function setMetadata(bytes memory newMetadata) external",

  "function setPrice(address _token, uint256 _price) external",
  "function getPrice() public view returns (address token, uint256 price)",

  "function getNonce() public view returns (uint256 nonce)",
  "function commit(address commiter,  bytes32 commitment, uint256 amount, bytes calldata signature) external",
]);

export const contractFactoryAbi = parseAbi([
  "function clone(address impl, bytes32 salt, bytes memory initData) external returns (address deployed)",
  "function predictClonedAddress(bytes32 salt) external view returns (address)",
]);

export const multicall3Abi = parseAbi([
  "struct Call { address target; bytes callData; }",
  "function aggregate(Call[] calldata calls) public payable returns (uint256 blockNumber, bytes[] memory returnData)"
]);

export interface ICall {
  target: Address,
  callData: Hex,
}

export function calldataInitData(
  owner: Address,
  metadataHash: Hex,
  token: Address,
  price: bigint
) {
  return encodeFunctionData({
    abi: dataRepoAbi,
    functionName: "initialize",
    args: [owner, metadataHash, token, price],
  });
}

export function calldataPredictAddress(initData: Hex) {
  const salt = keccak256(initData);
  return encodeFunctionData({
    abi: contractFactoryAbi,
    functionName: "predictClonedAddress",
    args: [salt],
  });
}

export function calldataClone(initData: Hex) {
  const salt = keccak256(initData);
  return encodeFunctionData({
    abi: contractFactoryAbi,
    functionName: "clone",
    args: [contractAddress.DataRepo as Address, salt, initData],
  });
}

export function calldataGetNonce() {
  return encodeFunctionData({
    abi: dataRepoAbi,
    functionName: "getNonce",
  });
}

export function calldataSetMetadata(newMetadata: Hex) {
  return encodeFunctionData({
    abi: dataRepoAbi,
    functionName: "setMetadata",
    args: [newMetadata],
  });
}

export function calldataMulticall(calls: ICall[]) {
  return encodeFunctionData({
    abi: multicall3Abi,
    functionName: "aggregate",
    args: [calls],
  });
}