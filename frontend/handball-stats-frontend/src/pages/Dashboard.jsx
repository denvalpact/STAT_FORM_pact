import { useEffect, useState } from 'react';
import api from '../api/api';
import { Typography, Grid } from '@mui/material';
import MatchCard from '../components/MatchCard'; // Assuming MatchCard is a component in your project

const Dashboard = () => {
    const [matches, setMatches] = useState([]);

    useEffect(() => {
        const fetchMatches = async () => {
            try {
                const response = await api.get('matches/');
                setMatches(response.data);
            } catch (error) {
                console.error('Error fetching matches:', error);
            }
        };
        fetchMatches();
    }, []);

    return (
        <div>
            <Typography variant="h4" gutterBottom>
                Upcoming Matches
            </Typography>
            <Grid container spacing={3}>
                {matches.map((match) => (
                    <Grid item xs={12} sm={6} key={match.id}>
                        <MatchCard match={match} />
                    </Grid>
                ))}
            </Grid>
        </div>
    );
};

export default Dashboard;