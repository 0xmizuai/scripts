import type { Address, Hex } from 'viem';
import type { DAMetadataRequest } from './utils/types';

import superagent from "superagent";
import { encodeFunctionData, keccak256, toBytes } from 'viem';

import { contractAddress, serverHosts } from './utils/config';
import { getKmsWalletClinet } from './utils/client';

import { contractFactoryAbi, dataRepoAbi, multicall3Abi, type ICall } from './utils/contract';
import { makeSalt, predictAddress } from './utils/predictAddress';

export const composeRepoCreation = async (category: string): Promise<[DAMetadataRequest, ICall]> => {
  const repoMetadata = {
    title: `Dolma - ${category}`,
    description: `This is a shard of Dolma about ${category}`,
    category: category,
    validationRules: []
  };

  const metadataHash = keccak256(toBytes(JSON.stringify(repoMetadata)));
  const initData = encodeFunctionData({
    abi: dataRepoAbi,
    functionName: 'initialize',
    args: [
      "0x0069f8e371b71f7996523c22bae7ea221666f06c" as Address,
      metadataHash,
      contractAddress.MizuPoints as Address,
      0n  
    ],
  });

  const address = await predictAddress(initData);

  return [
    {
      address, 
      title: repoMetadata.title,
      description: repoMetadata.description,
      category: repoMetadata.category,
      validationRules: repoMetadata.validationRules
    },
    {
      target: contractAddress.ContractFactory as Address,
      callData: encodeFunctionData({
        abi: contractFactoryAbi,
        functionName: 'clone',
        args: [
          contractAddress.DataRepo as Address,
          makeSalt(initData),
          initData
        ],
      })
    }
  ];
};

export const sendDARequest = async (request : DAMetadataRequest): Promise<Hex> => {
  const response = await superagent
    .post(`${serverHosts.da}/write/repo_metadata`)
    .send(request);
  
  const hash = JSON.parse(response.text)["data"]["hash"] as string;
  return `0x${hash}`
}

const categories = ["Science", "Technology", "Business", "Health", "Education", "Home and Hobby", "Arts and Entertainment", "Finance", "Religion and Spirituality", "Sports", "Leisure", "Society", "Design", "Environment", "History", "Journalism", "Law", "Linguistics", "Medicine", "Military", "Mining", "Nonprofits", "Philosophy", "Professional Development", "Psychology", "Publishing", "Retail", "Safety", "Science General", "Security", "Social Media", "Sociology", "Government Services", "Media", "Cultural", "Travel and Tourism", "Transportation", "Urban Development", "Visual Arts", "Volunteering", "Wellness", "Nature", "Wine and beverages", "Writing", "Zoology", "Antiques and Collectibles", "Research and Development", "Dance", "Entrepreneurship", "Legal", "Personal development", "Home Decor", "Recreation", "Consumer goods and Manufacturing", "Industrial", "Hobbies", "Professional services", "Human Resources", "Literature", "Family", "Marine", "Religion and Spiritual", "Shopping", "Government", "Social Issues", "Cognitive Science", "Event Planning", "Biotechnology", "Communications", "Pets", "Culture and Society", "Environmental Management and Recreation", "Finance and Accounting", "Entertainment and Media Services", "Healthcare and Medicine", "Community and Social Services", "Religion and Metaphysics", "Safety and Security", "Education and Learning", "Art and Design", "Transport and Shipping", "Personal Technology and Telecommunication", "Data and Programming", "Mindfulness and Well-being", "Food and Beverage", "Project Management", "Animal Care", "Beauty and Cosmetics", "Earth Sciences", "Legal Studies", "Hospitality", "Photography", "Arts and Crafts", "Consumer Goods", "Software", "Community & Sociology", "Engineering", "Gaming", "Mental Health", "Social Rules & Etiquettes", "Data Science", "Maternity & Childcare", "Maintenance", "Optics & Visual Effects", "Religion & Philosophy", "Sports & Leisure", "Climate & Environment Sciences", "Biologic Sciences", "Food & Hospitality", "Body Art & Modification", "Architecture & Planning", "Genres", "Drug Treatment", "Comedy", "Typography", "Sewing", "Adventure", "Alternative Health", "Measurement", "AnimalCare", "Architecture", "Arts", "AutomobileIndustry", "FoodAndDrinks", "Bicycling", "BioMedResearch", "Geography", "Tourism", "Brewing", "EducationalLife", "Career", "Entertainment", "Chemistry", "ChildCare", "Religion", "Cleaning", "ClimateChange", "IT", "CoffeeCulture", "Collections", "Comics", "CommunityDevelopment", "CompanyInfo", "ComputationalSciences", "Conference", "ConflictManagement", "ConsumerReports", "Currency", "CustomerService", "Disabilities", "DisasterManagement", "Diversity", "Dolls", "DrugUse", "Economy", "ElderlyCare", "Emergency", "EmotionalWellness", "Fishing", "Games", "Gambling", "Geneology", "GenderStudies", "Policy", "Grief", "Handicrafts", "Hardware", "Healing", "Educational", "Home", "HR", "IndustrialDesign", "Industry", "Ethics", "Fabrication", "InternationalAffairs", "Job and Career", "Languages", "Law and Justice", "Leadership and Management", "Insurance", "Life Skills and Self Help", "Life and Biological Sciences", "Lifestyle and Leisure", "Linguistics and Communication", "Engineering and Mechanics", "Operations", "Sports and Recreation", "Medical and Health", "Earth and Environmental Sciences", "Art and Modeling", "Transportation and Vehicles", "Arts and Culture", "Information Technology", "Business and Commerce", "Psychology and Behavior", "Public Affairs", "Real Estate and Housing", "Relationships and Society", "Animal Care and Behavior", "Media and Entertainment", "Social Media and Online Presence", "Professional Services", "Human Resources and Workplace", "Events and Celebrations", "Politics and Government", "Statistics", "Aeronautics and Space", "Agriculture and Farming", "Amusement and Theme Parks", "History and Civilizations", "Advertising and Marketing", "Accidents and Safety", "Power and Energy", "Seminars and Workshops", "Lifestyle", "Audio", "Automobiles", "Healthcare", "Holidays", "Cultural Studies", "Cuisine", "Counselling", "Communication", "Technical", "Electrical Engineering", "Homeopathy", "Homeschooling", "Interior Design", "Motor Sports", "Psychic", "Travel", "Computers & Technology", "Home & Family", "Local", "Media & Entertainment", "Social", "Criminal Justice", "Natural", "News & Media", "Special Needs & Services", "Travel & Transportation", "Software & Systems", "Hospitality & Recreation", "Science & Research", "Art", "Housing", "Management", "Politics", "Services", "Construction", "Consumer Protection", "Automotive", "Spirituality", "Animals", "Food", "Music", "Fashion", "Culture", "Property & Real Estate", "Sports & Fitness", "Veterinary", "Consultation", "Media Production", "Luxury Goods", "Law & Legislation", "Customer Service", "Performing Arts", "Sciences", "Outdoor & Nature-related", "Miscellaneous", "Sport", "Service", "Medical", "Weather", "Personal Care", "Organization"];


let calls: ICall[] = [];

for (const category of categories) {
  const [daRequest, call] = await composeRepoCreation(category);
  calls.push(call);
  const hash = await sendDARequest(daRequest);
  console.log("HASH", hash);
}

// await Bun.write('./all_tx.json', JSON.stringify(calls))

// // sending 10 in a batch
// let count = 0;
// let callBuffer: ICall[] = [];
// console.log("Sending", calls.length)
// for (const call of calls) {
//   count++;
//   callBuffer.push(call);
//   if (count % 10 === 0) {
//     const _ = await sendContractCallBatch(callBuffer);
//     callBuffer = [];
//   }
// }

// // send the rest of em
// console.log("Sending The Remaining", callBuffer.length)
// const _ = await sendContractCallBatch(callBuffer);