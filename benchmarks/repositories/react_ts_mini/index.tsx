import React, { useEffect, useState } from 'react';
import { ApiClient } from './api';
import { UserProfile } from './types';

const client = new ApiClient('/api/v1');

export const UserCard: React.FC<{ userId: string }> = ({ userId }) => {
    const [user, setUser] = useState<UserProfile | null>(null);

    useEffect(() => {
        client.fetchUserProfile(userId).then(res => setUser(res.data));
    }, [userId]);

    if (!user) return <div>Loading...</div>;

    return (
        <div className="user-profile-card">
            <h3>{user.username}</h3>
            <p>{user.email}</p>
            <span>Role: {user.role}</span>
        </div>
    );
};
