// Run with javascript_tool on a fantasy.espn.com page where Aidan is signed in to ESPN.
// Returns 100,000 spaces + '@@' + JSON, so the tool saves it to a file: take the text after the first '@@'
// (if the saved text is a JSON-quoted string, decode it first). Keys: a = $kullz FF, b = Boy Men Feet Balls.
// Each league: sc = ESPN's current week, tn = team names, games = [awayId, homeId], ros[teamId] = rows of
// [lineupSlotId, name, NFL team, bye week, injuryStatus, ESPN projection, points scored (null if not played), defaultPositionId].
(async () => {
const Y = new Date().getMonth() < 2 ? new Date().getFullYear() - 1 : new Date().getFullYear();
const base = `https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/${Y}`;
const pro = await fetch(`${base}?view=proTeamSchedules_wl`, {credentials: 'include'}).then(r => r.json());
const teams = {}; for (const t of pro.settings.proTeams) teams[t.id] = [t.abbrev.toUpperCase(), t.byeWeek];
async function lg(id) {
  const s = await fetch(`${base}/segments/0/leagues/${id}?view=mTeam&view=mStatus&view=mSettings`, {credentials: 'include'}).then(r => r.json());
  if (!s.status) throw new Error('ESPN refused league ' + id + ' (signed out?)');
  const sp = s.status.currentMatchupPeriod, sc = s.scoringPeriodId;
  const m = await fetch(`${base}/segments/0/leagues/${id}?view=mMatchup&view=mMatchupScore&view=mRoster&scoringPeriodId=${sc}`, {credentials: 'include'}).then(r => r.json());
  const tn = {}; for (const t of s.teams) tn[t.id] = (t.name || ((t.location || '') + ' ' + (t.nickname || ''))).trim();
  const ros = {};
  for (const t of m.teams) ros[t.id] = ((t.roster && t.roster.entries) || []).map(e => {
    const p = e.playerPoolEntry.player, st = p.stats || [];
    const pr = st.find(x => x.statSourceId === 1 && x.scoringPeriodId === sc && x.statSplitTypeId === 1);
    const ac = st.find(x => x.statSourceId === 0 && x.scoringPeriodId === sc && x.statSplitTypeId === 1);
    return [e.lineupSlotId, p.fullName, (teams[p.proTeamId] || ['FA'])[0], (teams[p.proTeamId] || [0, 0])[1], p.injuryStatus || '',
            pr ? Math.round(pr.appliedTotal * 10) / 10 : null, ac ? Math.round(ac.appliedTotal * 10) / 10 : null, p.defaultPositionId];
  });
  const games = m.schedule.filter(g => g.matchupPeriodId === sp).map(g => [g.away && g.away.teamId, g.home && g.home.teamId]);
  return {id, sp, sc, tn, games, ros};
}
const out = {a: await lg(80445470), b: await lg(810927169)};
return ' '.repeat(100000) + '@@' + JSON.stringify(out);
})()
