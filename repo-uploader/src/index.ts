import { createEmptyNewRepo } from './create-repo';
import { setMetadata } from './set-metadata';

const main = async () => {
  const title = 'Customer Support Agent Conversations2';
  const description = 'This is a sample data repo for customer support agent conversations';
  const validationRule = [
    'data commited must contains a conversation between a customer support agent and a customer',
    'the customer support agent should always be polite',
    'the customer is slightly aggressive',
  ];

  await createEmptyNewRepo(2619 + 300);
  // await createNewRepo(title, description, validationRule);
  // await setMetadata("0x75A92140F1B8943c3c0E0d0c9190762129f84F93", "new metadata");
};

main().catch(console.error);
