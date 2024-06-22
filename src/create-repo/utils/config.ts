export const contractAddress = {
  "ContractFactory": "0x405499443d0B76A1D994557a23A99CB8bD86C3e9", // deply new 
  "ContractProxy": "0x1cA7A9849dd15C46582DD38a252BB006f23fcE61", 
  "EventIndexer": "0xD3527c8C4f8d7979C77b847B57B22e1f37D73E4e", // emit events
  "DataRepo": "0x353fF5D2eE167cB8A97DF6d0C4da12F9eE4b1A0B", // impl 
  "MizuPoints": "0x82Ef318a759cEaf7B41d261CBa3B9BbCaeA72DdA", //erc20
  "Multicall3": "0xcA11bde05977b3631167028862bE2a173976CA11",
}

// export const serverHosts = {
//   signer: "https://signer.voda.build",
//   da: "https://da.voda.build",
//   inference: "https://inference.voda.build",
// };

export const serverHosts = {
  signer: "https://signer.voda.build",
  da: "http://127.0.0.1:3031",
  inference: "https://inference.voda.build",
};

export const config = {
  dataRepoOwner: process.env.DATA_REPO_OWNER!,
  infuraRpcUrl: process.env.INFURA_RPC_URL!,
};
