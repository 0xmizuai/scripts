import { createNewRepo } from './createrepo';

const main = async () => {
  const title = 'Customer Support Agent Conversations2';
  const description = 'This is a sample data repo for customer support agent conversations';
  const validationRule = [
    'data commited must contains a conversation between a customer support agent and a customer',
    'the customer support agent should always be polite',
    'the customer is slightly aggressive',
  ];

  await createNewRepo(title, description, validationRule);
};

main().catch(console.error);
