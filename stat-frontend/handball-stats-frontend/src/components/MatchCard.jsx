import React from 'react';
import { 
import { 
import { useNavigate } from 'react-router-dom';
import { format } from 'date-fns';

Card, 
CardContent, 
Typography, 
Chip, 
Stack, 
Button, 
Divider,
Avatar,
Box
} from '@mui/material';
SportsHandball, 
Timer, 
Event, 
People, 
ArrowForward 
} from '@mui/icons-material';

const MatchCard = ({ match }) => {
const navigate = useNavigate();

// Calculate match status and time display
const getMatchStatus = () => {
    if (match.status === 'FT') return 'Finished';
    if (match.status === 'HT') return 'Half Time';
    if (match.status === 'NS') return 'Not Started';
    return 'In Progress';
};

const getMatchTime = () => {
    if (match.status === 'NS') return format(new Date(match.date), 'HH:mm');
    if (match.status === 'FT') return 'FT';
    return `${Math.floor(match.current_time / 60)}:${(match.current_time % 60).toString().padStart(2, '0')}`;
};

return (
    <Card 
        sx={{ 
            minWidth: 300,
            maxWidth: 400,
            borderRadius: 2,
            boxShadow: 3,
            transition: 'transform 0.2s',
            '&:hover': {
                transform: 'scale(1.02)',
                boxShadow: 4
            }
        }}
    >
        <CardContent>
            {/* Match Header */}
            <Box sx={{ 
                display: 'flex', 
                justifyContent: 'space-between',
                alignItems: 'center',
                mb: 1
            }}>
                <Chip 
                    label={getMatchStatus()}
                    color={
                        match.status === 'FT' ? 'default' :
                        match.status === 'HT' ? 'warning' :
                        match.status === 'NS' ? 'secondary' : 'primary'
                    }
                    size="small"
                />
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Timer fontSize="small" sx={{ mr: 0.5 }} />
                    <Typography variant="body2">
                        {getMatchTime()}
                    </Typography>
                </Box>
            </Box>

            {/* Teams and Score */}
            <Box sx={{ textAlign: 'center', my: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                    <Avatar 
                        sx={{ 
                            bgcolor: 'primary.main',
                            width: 40, 
                            height: 40,
                            mr: 2
                        }}
                    >
                        {match.home_team.name.charAt(0)}
                    </Avatar>
                    
                    <Typography variant="h5" component="div">
                        {match.home_score} - {match.away_score}
                    </Typography>
                    
                    <Avatar 
                        sx={{ 
                            bgcolor: 'secondary.main',
                            width: 40, 
                            height: 40,
                            ml: 2
                        }}
                    >
                        {match.away_team.name.charAt(0)}
                    </Avatar>
                </Box>
                
                <Typography variant="subtitle1" color="text.secondary">
                    {match.home_team.name} vs {match.away_team.name}
                </Typography>
            </Box>

            <Divider sx={{ my: 1 }} />

            {/* Match Details */}
            <Stack spacing={1} sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Event fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />
                    <Typography variant="body2">
                        {format(new Date(match.date), 'MMM dd, yyyy')}
                    </Typography>
                </Box>
                
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <People fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />
                    <Typography variant="body2">
                        {match.referees.length} referees assigned
                    </Typography>
                </Box>
                
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <SportsHandball fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />
                    <Typography variant="body2">
                        {match.events?.length || 0} events recorded
                    </Typography>
                </Box>
            </Stack>

            {/* Action Buttons */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Button 
                    size="small" 
                    variant="outlined"
                    onClick={() => navigate(`/matches/${match.id}/stats`)}
                >
                    View Stats
                </Button>
                
                <Button 
                    size="small" 
                    variant="contained"
                    endIcon={<ArrowForward />}
                    onClick={() => navigate(`/matches/${match.id}`)}
                    disabled={match.status === 'NS'}
                >
                    {match.status === 'FT' ? 'Review' : 'Live View'}
                </Button>
            </Box>
        </CardContent>
    </Card>
);
};

// Default props for the component
MatchCard.defaultProps = {
match: {
    id: 1,
    home_team: { name: 'Home Team' },
    away_team: { name: 'Away Team' },
    home_score: 0,
    away_score: 0,
    date: new Date().toISOString(),
    status: 'NS',
    current_time: 0,
    referees: [],
    events: []
}
};

export default MatchCard;