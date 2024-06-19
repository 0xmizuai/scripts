import { createNewRepo } from './create-repo';
import { setMetadata } from './set-metadata';
export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
const main = async () => {
  // const title = 'Customer Support Agent Conversations2';
  // const description = 'This is a sample data repo for customer support agent conversations';
  // const validationRule = [
  //   'data commited must contains a conversation between a customer support agent and a customer',
  //   'the customer support agent should always be polite',
  //   'the customer is slightly aggressive',
  // ];

  for (let i = 302; i <= 1442; i++) {
    try {
      await createNewRepo();
      console.log(`Repo ${i} created successfully`);
    } catch (error) {
      console.error(`Error creating repo ${i}:`, error);
    }
    
    await sleep(1000);
  }
  // await createNewRepo();
  // await setMetadata("0x75A92140F1B8943c3c0E0d0c9190762129f84F93", "new metadata");
};

main().catch(console.error);
