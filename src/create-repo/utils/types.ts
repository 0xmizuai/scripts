import type { Address } from "viem";

export interface DAMetadataRequest {
    address: Address,
    title: string,
    description: string,
    category: string,
    validationRules: string[]
}