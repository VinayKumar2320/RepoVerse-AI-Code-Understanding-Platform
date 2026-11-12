import { UserProfile, ApiResponse } from './types';

export class ApiClient {
    private baseUrl: string;

    constructor(baseUrl: string) {
        this.baseUrl = baseUrl;
    }

    async fetchUserProfile(id: string): Promise<ApiResponse<UserProfile>> {
        const response = await fetch(`${this.baseUrl}/users/${id}`);
        const data = await response.json();
        return {
            data,
            status: response.status,
            timestamp: new Date().toISOString()
        };
    }
}
