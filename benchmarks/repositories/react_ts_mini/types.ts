export interface UserProfile {
    id: string;
    username: string;
    email: string;
    role: 'admin' | 'member';
}

export interface ApiResponse<T> {
    data: T;
    status: number;
    timestamp: string;
}
