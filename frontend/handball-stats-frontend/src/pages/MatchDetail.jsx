import React, { useEffect, useRef, useState } from "react";
import "./MatchDetail.css"; // You can move the CSS from the HTML to this file

const initialPlayers = {
    A: Array.from({ length: 16 }, (_, i) => ({
        id: i + 1,
        name: `Player A${i + 1}`,
        number: [7, 9, 11, 12, 5, 8, 10, 13, 14, 15, 16, 17, 18, 19, 20, 21][i],
        goals: 0,
        assists: 0,
        twoMinutes: 0,
        yellowCards: 0,
        redCard: false,
        steals: 0,
        blocks: 0,
        turnovers: 0,
    })),
    B: Array.from({ length: 16 }, (_, i) => ({
        id: i + 1,
        name: `Player B${i + 1}`,
        number: i + 1,
        goals: 0,
        assists: 0,
        twoMinutes: 0,
        yellowCards: 0,
        redCard: false,
        steals: 0,
        blocks: 0,
        turnovers: 0,
    })),
};

const periodLabels = {
    "1H": "Half-time(30')",
    "2H": "End of 60'",
    ET1: "1st extra time",
    ET2: "2nd extra time",
};

export default function MatchDetail() {
    const [players, setPlayers] = useState(initialPlayers);
    const [gameState, setGameState] = useState({
        seconds: 0,
        period: "1H",
        isTwoMinuteSuspension: false,
        suspensionTeam: null,
        suspensionEndTime: 0,
        timeouts: { A: 3, B: 3 },
        isTimeoutActive: false,
        timeoutTeam: null,
        timeoutStartTime: 0,
        timeoutEndTime: 0,
    });
    const [eventType, setEventType] = useState("GOAL");
    const [eventTeam, setEventTeam] = useState("A");
    const [eventPlayer, setEventPlayer] = useState("");
    const [timeoutTimers, setTimeoutTimers] = useState({ A: "", B: "" });
    const timerRef = useRef();
    const timeoutIntervalRef = useRef();

    // Timer for match time
    useEffect(() => {
        timerRef.current = setInterval(() => {
            setGameState((prev) => {
                let next = { ...prev, seconds: prev.seconds + 1 };
                // Period logic
                if (next.seconds < 1800) next.period = "1H";
                else if (next.seconds < 3600) next.period = "2H";
                else if (next.seconds < 3900) next.period = "ET1";
                else next.period = "ET2";
                // Suspension logic
                if (
                    next.isTwoMinuteSuspension &&
                    next.seconds >= next.suspensionEndTime
                ) {
                    next.isTwoMinuteSuspension = false;
                    next.suspensionTeam = null;
                }
                // Timeout timer
                if (
                    next.isTimeoutActive &&
                    next.seconds >= next.timeoutEndTime
                ) {
                    next.isTimeoutActive = false;
                    next.timeoutTeam = null;
                    setTimeoutTimers({ A: "", B: "" });
                }
                return next;
            });
        }, 1000);
        return () => clearInterval(timerRef.current);
    }, []);

    // Timeout timer display
    useEffect(() => {
        if (gameState.isTimeoutActive && gameState.timeoutTeam) {
            timeoutIntervalRef.current = setInterval(() => {
                setTimeoutTimers((prev) => {
                    const team = gameState.timeoutTeam;
                    const remaining =
                        gameState.timeoutEndTime - gameState.seconds > 0
                            ? gameState.timeoutEndTime - gameState.seconds
                            : 0;
                    const min = Math.floor(remaining / 60);
                    const sec = remaining % 60;
                    return {
                        ...prev,
                        [team]: `${min}:${sec.toString().padStart(2, "0")}`,
                    };
                });
            }, 1000);
        } else {
            clearInterval(timeoutIntervalRef.current);
            setTimeoutTimers({ A: "", B: "" });
        }
        return () => clearInterval(timeoutIntervalRef.current);
        // eslint-disable-next-line
    }, [gameState.isTimeoutActive, gameState.timeoutTeam, gameState.timeoutEndTime, gameState.seconds]);

    // Helper: format match time
    function formatMatchTime() {
        const periodSeconds = gameState.seconds % 1800;
        const min = Math.floor(periodSeconds / 60);
        const sec = periodSeconds % 60;
        return `${min.toString().padStart(2, "0")}:${sec
            .toString()
            .padStart(2, "0")}`;
    }

    // Add event handler
    function handleAddEvent() {
        const num = parseInt(eventPlayer, 10);
        if (isNaN(num) || num < 1 || num > 99) {
            alert("Please enter a valid player number (1-99)");
            return;
        }
        const team = eventTeam;
        const playerIdx = players[team].findIndex((p) => p.number === num);
        if (playerIdx === -1) {
            alert(`Player ${num} not found in Team ${team}`);
            return;
        }
        if (players[team][playerIdx].redCard) {
            alert(
                `Player ${players[team][playerIdx].name} (${num}) already has a red card and cannot participate!`
            );
            return;
        }
        setPlayers((prev) => {
            const updated = { ...prev, [team]: [...prev[team]] };
            const player = { ...updated[team][playerIdx] };
            switch (eventType) {
                case "GOAL":
                case "7M":
                    player.goals += 1;
                    break;
                case "ASSIST":
                    player.assists += 1;
                    break;
                case "2MIN":
                    if (player.twoMinutes < 3) {
                        player.twoMinutes += 1;
                        if (player.twoMinutes >= 3) {
                            player.redCard = true;
                            alert(
                                `Player ${player.name} (${player.number}) received a red card for 3 two-minute suspensions!`
                            );
                        }
                    }
                    break;
                case "YELLOW":
                    if (player.yellowCards < 2) {
                        player.yellowCards += 1;
                        if (player.yellowCards >= 2) {
                            alert(
                                `Player ${player.name} (${player.number}) has received 2 yellow cards!`
                            );
                        }
                    }
                    break;
                case "STEAL":
                    player.steals += 1;
                    break;
                case "BLOCK":
                    player.blocks += 1;
                    break;
                case "TURNOVER":
                    player.turnovers += 1;
                    break;
                default:
                    break;
            }
            updated[team][playerIdx] = player;
            return updated;
        });
        setEventPlayer("");
    }

    // Timeout logic
    function handleTimeout(team) {
        if (gameState.timeouts[team] <= 0) {
            alert(`Team ${team} has no timeouts remaining!`);
            return;
        }
        if (gameState.isTimeoutActive) {
            alert("A timeout is already active!");
            return;
        }
        setGameState((prev) => ({
            ...prev,
            isTimeoutActive: true,
            timeoutTeam: team,
            timeouts: { ...prev.timeouts, [team]: prev.timeouts[team] - 1 },
            timeoutStartTime: prev.seconds,
            timeoutEndTime: prev.seconds + 60,
        }));
        alert(
            `Team ${team} called a timeout (1 minute). Remaining timeouts: ${
                gameState.timeouts[team] - 1
            }`
        );
    }

    // Suspension toggle
    function handleToggleSuspension() {
        setGameState((prev) => {
            if (!prev.isTwoMinuteSuspension) {
                return {
                    ...prev,
                    isTwoMinuteSuspension: true,
                    suspensionTeam: eventTeam,
                    suspensionEndTime: prev.seconds + 120,
                };
            } else {
                return {
                    ...prev,
                    isTwoMinuteSuspension: false,
                    suspensionTeam: null,
                };
            }
        });
    }

    // Render team table
    function renderTeamTable(team) {
        return (
            <table className="stat-table">
                <thead>
                    <tr>
                        <th className="small-col">No.</th>
                        <th className="name-col">Name</th>
                        <th className="small-col">Shirt</th>
                        <th className="small-col">Goals</th>
                        <th className="small-col">Assists</th>
                        <th className="small-col">2'</th>
                        <th className="small-col">Yellow</th>
                        <th className="small-col">Red</th>
                        <th className="small-col">Steals</th>
                        <th className="small-col">Blocks</th>
                        <th className="small-col">Turnovers</th>
                    </tr>
                </thead>
                <tbody>
                    {players[team].map((player, idx) => (
                        <tr key={player.id} className={player.redCard ? "red-card" : ""}>
                            <td>{idx + 1}</td>
                            <td>{player.name}</td>
                            <td>{player.number}</td>
                            <td>{player.goals}</td>
                            <td>{player.assists}</td>
                            <td>{player.twoMinutes}</td>
                            <td className={player.yellowCards > 0 ? "yellow-card" : ""}>
                                {player.yellowCards}
                            </td>
                            <td>{player.redCard ? "X" : ""}</td>
                            <td>{player.steals}</td>
                            <td>{player.blocks}</td>
                            <td>{player.turnovers}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        );
    }

    return (
        <div className="form-container">
            <div className="header">ENHANCED MATCH STATISTICS</div>
            <div className="match-info">
                <div className="team-info">
                    <div>
                        <strong>Team A</strong> vs <strong>Team B</strong>
                    </div>
                    <div>
                        <strong>Date:</strong> <span id="match-date">2023-11-15</span>
                    </div>
                </div>
                <div>
                    <strong>Match No.:</strong> <span id="match-number">10765</span>
                </div>
            </div>
            {/* Timeout Controls */}
            <div className="timeout-controls">
                <div className="timeout-team">
                    <span>Team A Timeouts:</span>
                    <span className="timeout-count">{gameState.timeouts.A}</span>
                    <button
                        className={`timeout-button${
                            gameState.timeouts.A <= 0 ||
                            gameState.isTimeoutActive
                                ? " timeout-disabled"
                                : ""
                        }${
                            gameState.isTimeoutActive && gameState.timeoutTeam === "A"
                                ? " timeout-active"
                                : ""
                        }`}
                        onClick={() => handleTimeout("A")}
                        disabled={gameState.timeouts.A <= 0 || gameState.isTimeoutActive}
                    >
                        Call Timeout
                    </button>
                    <span className="timeout-timer">{timeoutTimers.A}</span>
                </div>
                <div className="timeout-team">
                    <span>Team B Timeouts:</span>
                    <span className="timeout-count">{gameState.timeouts.B}</span>
                    <button
                        className={`timeout-button${
                            gameState.timeouts.B <= 0 ||
                            gameState.isTimeoutActive
                                ? " timeout-disabled"
                                : ""
                        }${
                            gameState.isTimeoutActive && gameState.timeoutTeam === "B"
                                ? " timeout-active"
                                : ""
                        }`}
                        onClick={() => handleTimeout("B")}
                        disabled={gameState.timeouts.B <= 0 || gameState.isTimeoutActive}
                    >
                        Call Timeout
                    </button>
                    <span className="timeout-timer">{timeoutTimers.B}</span>
                </div>
            </div>
            <div className="time-markers">
                {Object.entries(periodLabels).map(([key, label]) => (
                    <div
                        key={key}
                        id={`period-${key}`}
                        className={gameState.period === key ? "active-period" : ""}
                    >
                        {label}
                    </div>
                ))}
            </div>
            <div className="controls">
                <strong>Add Event:</strong>
                <select
                    id="event-type"
                    value={eventType}
                    onChange={(e) => setEventType(e.target.value)}
                >
                    <option value="GOAL">Goal</option>
                    <option value="7M">7m Goal</option>
                    <option value="ASSIST">Assist</option>
                    <option value="2MIN">2' Suspension</option>
                    <option value="YELLOW">Yellow Card</option>
                    <option value="STEAL">Steal</option>
                    <option value="BLOCK">Block</option>
                    <option value="TURNOVER">Turnover</option>
                </select>
                <select
                    id="event-team"
                    value={eventTeam}
                    onChange={(e) => setEventTeam(e.target.value)}
                >
                    <option value="A">Team A</option>
                    <option value="B">Team B</option>
                </select>
                <input
                    type="number"
                    id="event-player"
                    placeholder="Player No."
                    min={1}
                    max={99}
                    style={{ width: 50 }}
                    value={eventPlayer}
                    onChange={(e) => setEventPlayer(e.target.value)}
                />
                <button id="add-event" onClick={handleAddEvent}>
                    Add
                </button>
                <span id="game-time" style={{ marginLeft: 20 }}>
                    <strong>Time:</strong>{" "}
                    <span id="match-time">{formatMatchTime()}</span>
                    <span id="current-period" className="active-period">
                        {gameState.period}
                    </span>
                </span>
                <button
                    id="toggle-suspension"
                    className={gameState.isTwoMinuteSuspension ? "suspension-active" : ""}
                    onClick={handleToggleSuspension}
                >
                    {gameState.isTwoMinuteSuspension
                        ? `2' Suspension (${gameState.suspensionTeam})`
                        : "2' Suspension Inactive"}
                </button>
            </div>
            {/* Two Column Layout */}
            <div className="columns-container">
                <div className="team-column team-a-column">
                    <div className="team-title">TEAM A</div>
                    {renderTeamTable("A")}
                </div>
                <div className="team-column team-b-column">
                    <div className="team-title">TEAM B</div>
                    {renderTeamTable("B")}
                </div>
            </div>
            <div className="match-info" style={{ marginTop: 10 }}>
                <div>
                    <strong>Referees:</strong>{" "}
                    <span id="referee1">John Smith</span>,{" "}
                    <span id="referee2">Michael Johnson</span>
                </div>
                <div>
                    <strong>City:</strong> <span id="city">Berlin</span>
                </div>
            </div>
        </div>
    );
}