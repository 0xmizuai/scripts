import type { Address, Hex } from "viem";
import { parseAbi } from "viem";

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
