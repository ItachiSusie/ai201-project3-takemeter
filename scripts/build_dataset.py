"""
build_dataset.py — Build the full 200+ example dataset by:
  1. Using whatever was collected in raw_posts.csv
  2. Adding curated examples that represent each label category
     (researcher-generated posts matching real r/nba discourse patterns,
      clearly documented in planning.md and README AI usage section)

Usage:
    python scripts/build_dataset.py

Output:
    data/nba_dataset.csv  — final labeled dataset (200+ examples)
"""

import csv
import re
import html
from pathlib import Path

# ── Curated examples per label ───────────────────────────────────────────────
# These are researcher-generated posts that match real r/nba discourse patterns.
# Each example was designed to clearly exemplify one label category.
# Disclosed in README AI Usage section.

CURATED = [
    # ── ANALYSIS (structured argument + specific evidence) ────────────────────
    {"text": "Luka's pull-up three efficiency this postseason (.412) puts him in historically rare company. Only Steph Curry and Dirk have posted higher rates in a single playoff run at 5+ attempts per game. His release point is fundamentally higher than most pull-up shooters, which reduces the contest window for closing defenders.", "label": "analysis"},
    {"text": "People underestimate how much the Celtics' switch-everything defense depends on Porzingis. When he's off the floor, their defensive rating drops from 107.2 to 119.4. The system requires a 7-footer who can guard guards, and that's why the Pacers targeted him with off-ball screens in the fourth quarter.", "label": "analysis"},
    {"text": "Tyrese Haliburton's assist-to-turnover ratio (4.8) is better than any point guard in this postseason. More importantly, his turnovers happen almost entirely in transition — in halfcourt sets he's at 0.9 TO per game, which is elite. Teams are giving up trying to pressure him in set offense because it doesn't work.", "label": "analysis"},
    {"text": "The Thunder's drop coverage is designed around SGA's ability to recover late — they're willing to give up mid-range attempts because their data shows opponents shoot 38% on those versus 46% at the rim. This makes SGA's lateral quickness more valuable defensively than his raw block numbers suggest.", "label": "analysis"},
    {"text": "Nikola Jokic's true shooting percentage in the playoffs (.641) is the highest ever for a center with 20+ postseason games. His advantage isn't athleticism — it's that he converts at the same rate whether he's 5 feet or 18 feet from the basket, making it impossible for help defenses to load up on one zone.", "label": "analysis"},
    {"text": "The Warriors' dynasty was built around one tactical insight: at the time they drafted Steph, shooting percentage on catch-and-shoot threes was undervalued in player evaluation. They exploited that market inefficiency for four titles before every team adapted. The question now is what the next undervalued skill category is.", "label": "analysis"},
    {"text": "Giannis is shooting 71% at the rim this season but drops to 44% on floaters. His rim pressure is elite, but teams that can push him to the floater zone at 8-12 feet neutralize him effectively. This is why the Celtics keep switching matchups — they're trying to force him into that mid-range floater zone.", "label": "analysis"},
    {"text": "Anthony Davis' rebounding numbers drop significantly in fourth quarters (7.2 per 36 in Q1-3 vs 4.1 in Q4). This isn't fatigue — it's positioning. He tends to gamble on offensive boards in Q4, which leaves him out of defensive rebounding position. The Lakers lose 68% of their Q4 possessions when he misses a defensive rebound.", "label": "analysis"},
    {"text": "Kawhi Leonard's lateral quickness allows him to guard every position 1-5 in isolation. His defensive win shares per game are 0.27 — that's 15% higher than his next closest contemporary. What makes this remarkable is that it holds up even against guards, where his height disadvantage should matter.", "label": "analysis"},
    {"text": "The Lakers' spacing problem is structural: they have three players who need the ball in their hands to be effective (LeBron, AD, Austin Reaves) but none who can reliably space the floor as a catch-and-shoot option. Their corner three percentage as a team is 28.4%, which is the fourth-worst in the league.", "label": "analysis"},
    {"text": "Steph Curry's off-ball movement creates a measurable effect on his teammates' open-look frequency. When Steph is on the floor, Klay's catch-and-shoot opportunities increase by 2.3 per game because defenders have to track Curry through screens. This is the gravity effect in quantifiable terms.", "label": "analysis"},
    {"text": "Victor Wembanyama's block percentage (7.8%) is already in the historical top 10 for any player's second season. But the more interesting number is his post-block recovery rate — he blocks a shot and returns to defensive position before the next possession 89% of the time, which is what makes the Spurs' system work.", "label": "analysis"},
    {"text": "The Celtics' bench scoring differential is +8.4 per 100 possessions with Payton Pritchard on the floor, which is better than their starters' differential in most second-round series. He does one thing nobody else on the team does: catches and shoots off the dribble hand-off in under 0.6 seconds, which completely negates switching defenses.", "label": "analysis"},
    {"text": "Minnesota's defensive scheme under Chris Finch is the most complex in the league: they use five different coverages depending on the ball handler, and they switch coverages within a single possession based on who sets the screen. Their defensive rating in the fourth quarter (103.1) is the best in the playoffs because teams can't adjust at halftime to something that's constantly shifting.", "label": "analysis"},
    {"text": "Ja Morant's efficiency in transition (1.41 points per possession) is the highest in the league for players with 10+ transition touches per game. Where he struggles is in halfcourt isolation (0.82 PPP), which is below league average. Memphis wins when they can turn defense into fast breaks; they lose when teams slow the game down.", "label": "analysis"},
    {"text": "Donovan Mitchell's three-point volume (8.4 attempts per game) masks a concerning trend: his shot quality has declined each of the last three seasons. His corner three percentage is still elite (42%), but his above-the-break attempts — which make up 73% of his volume — have dropped from 38% to 33% over three years.", "label": "analysis"},
    {"text": "The Heat culture advantage is quantifiable: Miami's undrafted players outperform their draft-position expectations by an average of 4.2 WAR over their first contracts. This is the largest such differential in the league and it's been consistent for 15 years. Whatever Pat Riley's evaluation process is, it systematically identifies undervalued players.", "label": "analysis"},
    {"text": "OKC's young core is historically unprecedented: they have four players under 24 with a combined WAR of 18.3, which is higher than the 2011-12 Thunder at the same stage. The key difference is depth — the 2012 team had Durant and Westbrook as clear outliers, while this team's talent is more evenly distributed.", "label": "analysis"},
    {"text": "The Nuggets' pick-and-roll coverage against Jokic is uniquely difficult because traditional PnR defense assumes the roller wants to get to the rim. Jokic is equally dangerous at the elbow, the short roll, and the mid-post, meaning drop coverage, hedge, and switch all have exploitable weaknesses. There is no clean answer.", "label": "analysis"},
    {"text": "Boston's home court advantage is statistically significant: they're 31-6 at home in the last two regular seasons, but their away record is 22-19. The difference isn't effort or focus — their three-point percentage at home is 38.2% versus 35.1% on the road, which suggests crowd noise affects shot timing for the defense more than it affects the Celtics.", "label": "analysis"},
    {"text": "The question of whether load management works is empirically answerable: players who averaged 62-68 games per season in years 3-5 had a 23% lower rate of soft tissue injuries in years 6-10 compared to players who averaged 75+ games. The Spurs pioneered this because their medical staff ran the numbers in the early 2000s.", "label": "analysis"},
    {"text": "Draymond Green's non-scoring value is the hardest thing to capture in box scores. His on/off splits show a +7.3 defensive rating differential — when he's on the floor, the Warriors hold opponents to 108; when he's off, it's 115.3. No other non-scorer has a comparable impact on a team's defensive ceiling.", "label": "analysis"},
    {"text": "The Thunder have the youngest starting lineup in the playoffs since the 2012 Thunder, but their turnover rate (11.2%) is the lowest of any young team in that comparison set. Age typically correlates with turnovers because young players make poor decisions under pressure — OKC has somehow avoided this through their pace and shot selection.", "label": "analysis"},
    {"text": "Damian Lillard's playoff reputation problem is real but the data tells a more nuanced story. In playoff series where he's had a competent second star, his team advanced 6 of 7 times. In series where he was clearly the only All-Star, his teams went 1-6. The pattern suggests his supporting cast was the variable, not his clutch performance.", "label": "analysis"},
    {"text": "Miami's zone defense is particularly effective because Bam Adebayo can play the point of the zone while also hedging on drives. Most zones are vulnerable to the short corner — Miami's isn't because Adebayo can cover that position from two zones simultaneously. This is why teams with elite mid-range shooters struggle against them.", "label": "analysis"},

    # ── HOT_TAKE (bold opinion, minimal or no supporting evidence) ────────────
    {"text": "LeBron is the most overrated player in NBA history. His rings all came with elite help and he never won the hard way. Michael Jordan never needed a Big Three to get a championship.", "label": "hot_take"},
    {"text": "The NBA is completely soft now. Load management is just players being scared of real competition. The 90s players would never pull themselves out of a game because they were a little tired.", "label": "hot_take"},
    {"text": "Kawhi Leonard is the greatest two-way player of all time and it's not even close. Nobody can guard him and nobody plays defense like him. He's been underappreciated his entire career.", "label": "hot_take"},
    {"text": "Anyone who thinks Luka Doncic is a top 5 player right now is lying to themselves. He's never won anything meaningful and his defense is a liability. Great regular season stats, nothing more.", "label": "hot_take"},
    {"text": "The Warriors dynasty was luck. They got Steph cheap because nobody could evaluate shooting, and then Durant handed them two more rings. Take away KD and they're a good team, not a dynasty.", "label": "hot_take"},
    {"text": "Giannis is not and will never be the best player in the world. He can't shoot, he can't create in the halfcourt, and he disappears in big moments. The stats look great until they don't matter.", "label": "hot_take"},
    {"text": "The current generation of NBA players would get destroyed in the 1990s. The physicality was different, the defense was different, the travel calls were different. Stars today are protected by the league.", "label": "hot_take"},
    {"text": "Nikola Jokic is a system player and everybody knows it. Put him on a bad team with no shooters and his numbers collapse. His MVPs are a media narrative, not a reflection of real impact.", "label": "hot_take"},
    {"text": "Anthony Davis is the most underachieving superstar in NBA history. The talent is generational but the will to win isn't there. He disappears in big games and then gives excuses about his body.", "label": "hot_take"},
    {"text": "Kobe Bryant was a better player than LeBron James. Every single metric you could possibly care about, Kobe was better when it mattered. The historical revisionism around LeBron is absurd.", "label": "hot_take"},
    {"text": "The Thunder are overrated and their regular season success means nothing. Wait until they hit a real playoff run against experienced teams. Young teams always look great until they face adversity.", "label": "hot_take"},
    {"text": "Chet Holmgren is a franchise cornerstone and I'll die on this hill. Anyone who questions his ceiling isn't watching the same games I'm watching. He's going to be a Hall of Famer.", "label": "hot_take"},
    {"text": "Wembanyama will surpass LeBron as the greatest player of all time by the time he's 25. The talent is just different. We've never seen anything like this before and we need to stop comparing him to everyone.", "label": "hot_take"},
    {"text": "The Knicks are finally back and this is their year. I know I say this every season but this time is different. The pieces are in place. New York is going to the Finals.", "label": "hot_take"},
    {"text": "Devin Booker is more clutch than anyone in the league right now and stats don't even capture it. You have to watch the games. The eye test is more reliable than any metric for clutch performance.", "label": "hot_take"},
    {"text": "Jimmy Butler is the most mentally tough player in the NBA. He literally wills his teams to wins. Analytics can't measure heart and Jimmy Butler has more of it than anyone in the league.", "label": "hot_take"},
    {"text": "Scottie Barnes is going to be an All-Star for the next decade. The upside is elite and the Raptors are going to regret not building around him properly. Mark my words.", "label": "hot_take"},
    {"text": "The Celtics only win because of the system. Put any of those players on a different team and half of them are average starters at best. Coaching means everything and they benefit from it.", "label": "hot_take"},
    {"text": "Ja Morant's ceiling is higher than any guard in the league except Steph. His athleticism is generational. Once he matures mentally he's going to win multiple championships.", "label": "hot_take"},
    {"text": "The referees are ruining the NBA. Every big game has questionable calls that swing the outcome and everyone knows it but nobody wants to say it. The league is scripted.", "label": "hot_take"},
    {"text": "Stephen Curry is the greatest player of his generation, full stop. No argument. The championships, the records, the way he changed the game. LeBron isn't even close if you're being honest.", "label": "hot_take"},
    {"text": "Paul George is the most overrated player of the last decade. Consistently underperforms in big moments and then gets max contracts anyway. The media has always protected him.", "label": "hot_take"},
    {"text": "The Milwaukee Bucks made a massive mistake not building around Giannis differently. Khris Middleton was never the co-star they needed. They wasted two prime Giannis years.", "label": "hot_take"},
    {"text": "Trae Young is a stat compiler and nothing more. He puts up big numbers against teams that are already losing. In truly competitive series against elite defenses he always disappears.", "label": "hot_take"},
    {"text": "OKC is going to win a championship within three years or this run is a failure. They have too much talent to not win it all. Anything less is a disappointment given what they've assembled.", "label": "hot_take"},
    {"text": "Rudy Gobert is the most undeserving Defensive Player of the Year winner in history. He's just tall and blocks shots in a system designed to funnel everyone toward him. Take away the Spurs-style coverage and he's average.", "label": "hot_take"},
    {"text": "The NBA became unwatchable once they started calling every slight contact a foul. The game is for superstars now — everyone else just has to hope they don't breathe on the star player the wrong way.", "label": "hot_take"},
    {"text": "Carmelo Anthony should have a Finals ring. The 2009-11 Nuggets were a bad coaching decision away from the title and Melo was the best player on the floor in multiple series. History has been unfair to him.", "label": "hot_take"},
    {"text": "Kevin Durant is a top 3 player all time and the debate should be over. He can do literally everything on a basketball court. The ring discourse is poisoning the GOAT conversation.", "label": "hot_take"},
    {"text": "Zion Williamson will never reach his potential. His body isn't made for this game at the highest level and his diet and conditioning show he doesn't want it enough. Sad waste of talent.", "label": "hot_take"},

    # ── REACTION (immediate emotional response to specific event) ──────────────
    {"text": "THAT DUNK BY ANT OMFG HE JUST POSTERIZED A 7-FOOTER WHILE DRAWING THE FOUL WHAT", "label": "reaction"},
    {"text": "Can't believe we let that lead slip. Up 18 in the third and somehow we found a way to lose. This team breaks my heart every single year. I can't do this anymore.", "label": "reaction"},
    {"text": "Steph just hit back to back threes from 30+ feet like it was nothing. I've been watching basketball for 30 years and I've never seen shooting like this in my life.", "label": "reaction"},
    {"text": "GIANNIS WITH THE CHASE DOWN BLOCK AT THE END OF REGULATION!!!! HOW IS THIS MAN REAL", "label": "reaction"},
    {"text": "Refs deciding this one again. Third game in a row where a crucial call went against us in crunch time. This is getting embarrassing.", "label": "reaction"},
    {"text": "I literally screamed out loud when Lillard hit that three at the buzzer. My neighbors probably think something happened to me. What a game.", "label": "reaction"},
    {"text": "Did not see that trade coming at all. Just refreshed Twitter and my jaw dropped. How did we not see this coming?", "label": "reaction"},
    {"text": "Luka crying at the buzzer after that loss. Tough to watch. Whatever you think about his team or his personality, that's genuine heartbreak.", "label": "reaction"},
    {"text": "Oh my god Wemby just blocked THREE shots in one possession. I had to rewind it three times to make sure I actually saw what I thought I saw.", "label": "reaction"},
    {"text": "My team is down 3-1 in the series. I said I was going to stop watching after last year and here I am again watching them break my heart. Every year.", "label": "reaction"},
    {"text": "That block by Davis in OT was the greatest single defensive play I've seen in a decade. I stood up in my living room alone and cheered.", "label": "reaction"},
    {"text": "I cannot believe we lost by one point after that shot clock violation they called. That is going to haunt me for weeks.", "label": "reaction"},
    {"text": "Just woke up to see we traded [player]. I need to sit with this for a minute. Not happy. This came out of nowhere and I feel blindsided.", "label": "reaction"},
    {"text": "Tatum just put up 51 in a playoff game. I'm watching history unfold in real time and I need everybody to appreciate this moment.", "label": "reaction"},
    {"text": "CURRY FROM HALF COURT AT THE BUZZER AND IT WENT IN. THIS IS NOT REAL BASKETBALL. THIS MAN IS FROM ANOTHER DIMENSION.", "label": "reaction"},
    {"text": "I've never been more proud of this team even in a loss. They fought all the way back from 22 down and almost pulled it off. Incredible heart.", "label": "reaction"},
    {"text": "Watching LeBron carry this team tonight is making me emotional. He is 39 years old and doing things that shouldn't be possible. It won't last forever and I want to appreciate every game.", "label": "reaction"},
    {"text": "That injury looked bad. Really bad. Please be okay. Praying for him right now.", "label": "reaction"},
    {"text": "ESPN cut to commercial right as the game-winning shot went in and I watched it happen and then missed the replay. I am absolutely furious right now.", "label": "reaction"},
    {"text": "Game 7 tomorrow and I am already too anxious to sleep. This franchise will be the death of me. Let's go.", "label": "reaction"},
    {"text": "My son just saw his first playoff game in person tonight and his team won in overtime. I'm not gonna lie I teared up a little. This is what basketball is about.", "label": "reaction"},
    {"text": "What just happened. What just happened. Someone explain what just happened. I watched it live and I still don't understand what I saw.", "label": "reaction"},
    {"text": "Got to stop watching games at work. Just tried to suppress a reaction at my desk and failed completely. Coworkers are looking at me weird.", "label": "reaction"},
    {"text": "That fourth quarter is going to be in my nightmares. Blew a 15-point lead in 6 minutes. Against that team. In the playoffs. I genuinely do not understand how.", "label": "reaction"},
    {"text": "Jokic just hit an impossible fadeaway over two defenders with 3 seconds left and the whole arena went completely silent. The most surreal sports moment I've witnessed live.", "label": "reaction"},
    {"text": "My heart cannot take another overtime game. We've had five in this series. Five. I age about ten years every time we go to OT.", "label": "reaction"},
    {"text": "JOKER TRIPLE DOUBLE IN GAME 7 LET'S GOOOOO", "label": "reaction"},
    {"text": "I'm not okay right now. That shot was in and out. It was IN. I watched it go in and come out. That is not fair. I don't want to talk about it.", "label": "reaction"},
    {"text": "Just got home from the arena. My voice is completely gone. Incredible atmosphere tonight, even in a loss. Proud to be a fan of this team.", "label": "reaction"},
    {"text": "Three missed free throws with under a minute left and we lost by two. I'm going to bed. Don't talk to me. Good night.", "label": "reaction"},

    # ── Additional ANALYSIS examples ───────────────────────────────────────────
    {"text": "The reason Jokic wins MVPs over higher-usage players comes down to how his team's offensive rating changes when he sits. Denver drops from 119 to 105 per 100 possessions — a 14-point swing. No other player in the league creates that size of gap. The measure is impact, not usage.", "label": "analysis"},
    {"text": "KD's true shooting percentage in his prime (.644) is the highest ever for a volume scorer (18+ FGA per game). What's underappreciated is how he achieves it — 62% of his shots are off screens or on the move, meaning he's not just hunting mismatches but creating clean looks through movement.", "label": "analysis"},
    {"text": "The Spurs' five-out offense in the 2010s wasn't just beautiful — it was analytically sound. When all five players are spread to the three-point line, each player needs just 12 square feet of coverage, compared to 18 in a traditional offense. That spacing translates directly to a 4.2% improvement in shot quality.", "label": "analysis"},
    {"text": "What makes Harden's stepback so hard to defend is timing, not distance. He releases 0.14 seconds faster than the average guard on pull-up threes. That sounds trivial but it's the difference between a defender getting a hand in your face and closing out while you're already in your shot.", "label": "analysis"},
    {"text": "Joel Embiid's decline in Q4 efficiency (from 1.12 PPP in Q1-3 to 0.89 in Q4) isn't fatigue — it's scheme adjustment. Teams that have faced him multiple times in a series start blitzing his post catches in the fourth quarter. His PPP against double teams is 0.77, which is below average.", "label": "analysis"},
    {"text": "Memphis's drop in wins after Ja's injury isn't just his absence — it's a calibration failure. Their entire offensive system (pace, transition, corner three generation) is triggered by his ability to get into the paint. Without that threat, their 3-point shooting dropped from 36.8% to 33.1% on the same shot types.", "label": "analysis"},
    {"text": "Rudy Gobert's defensive value is best measured in rim deterrence, not blocks. When he protects the paint, opponents' rim FG% drops from 65% to 54% — that's a 11-point swing. His blocks are 2.1 per game but his deterred shots (attempts that were altered before release) are 4.7 per game based on spatial tracking data.", "label": "analysis"},
    {"text": "What's unusual about Tyrese Maxey's development is that his improvement came in his decision-making, not his athleticism. His turnover-to-assist ratio went from 1:1.8 to 1:3.4 between year 2 and year 4. Players don't typically make that kind of cognitive leap — most improvement at his level is physical.", "label": "analysis"},
    {"text": "The Suns' window opened and closed faster than any dynasty candidate in recent memory. They had the best record in the league in 2021-22 but couldn't convert it because their entire system was built on Chris Paul's IQ — which aged out faster than the roster around him. Youth or prime players but not both.", "label": "analysis"},
    {"text": "Draymond Green's defensive impact in the 2016 Finals was the difference in the series. He was the primary defender on LeBron James for 47 defensive possessions in Games 6-7, holding him to 0.81 PPP. Remove those stops and Golden State's comeback is mathematically impossible.", "label": "analysis"},
    {"text": "The three-point revolution changed who gets drafted more than it changed how teams play offense. From 2010-2015, teams drafted 8.2 shooters per year in the first two rounds. From 2019-2024, that number is 14.7. The downstream effect is that interior scorers without range are being devalued systematically.", "label": "analysis"},
    {"text": "Chicago's rebuild is structurally sound but the timeline is off. They have two players (Williams and White) in the 24-27 prime window, one player (LaVine) past his peak, and no developmental lottery talent. The roster is too good to tank for picks but not good enough to win. This is the treadmill problem.", "label": "analysis"},
    {"text": "The Warriors' advantage in clutch situations (.617 win% in games decided by 5 or fewer points) comes from their depth of motion offense — they have 7 players who can execute the same reads, so tired legs don't break the system. Teams that rely on hero ball in clutch time show variance; teams with systems show consistency.", "label": "analysis"},
    {"text": "Brook Lopez has been the most underrated piece of the Bucks dynasty. His screen-setting creates 3.1 open looks per game for his teammates, and his corner three shooting (41%) forces defenses to honor him even at 36. His value is systemic — it disappears on paper when you just look at his scoring line.", "label": "analysis"},
    {"text": "The reason the Knicks' rebuild is real this time is their draft and development infrastructure. Four of their current core players were second-round picks or undrafted. Their player development staff has a measurable track record now — that's a foundation, not a fluke.", "label": "analysis"},
    {"text": "Analytics teams in the NBA have known for 10 years that corner threes are more valuable than above-the-break threes (same 3 points, shorter distance, higher percentage). Yet only half the league has fully committed to corner-three generation. The reason is that corner spots require specific off-ball movement that older coaches haven't fully adopted.", "label": "analysis"},
    {"text": "LeBron's longevity is remarkable even by generational athlete standards. The average NBA player's athleticism peaks at 26 and declines measurably after 30. LeBron at 38 posted better rim pressure numbers than his 30-year-old self. This is what elite conditioning and body management looks like across a 20-year career.", "label": "analysis"},
    {"text": "Golden State's problems this season are structural. Their two-man game with Steph and Draymond still works, but their supporting cast's aging curves have crossed the threshold where they're a net drag rather than a net help. The Warriors need to decide whether to rebuild around Steph or acknowledge the window is closed.", "label": "analysis"},
    {"text": "Victor Wembanyama's wingspan-to-height ratio (8'5\" span for a 7'4\" player) is unprecedented in NBA history by three inches. This matters because defensive reach on rim protection scales with wingspan, not height. His effective defensive radius is approximately 15% larger than any center who has ever played.", "label": "analysis"},
    {"text": "Scottie Barnes' assist rate (15.4% in year 3) is higher than any comparable forward at the same age in the last decade. What's different about his playmaking is it comes primarily from the elbow — he's creating off middle drives, not from the perimeter. This is harder to defend because it requires the help defender to choose between the driver and the cutter.", "label": "analysis"},
    {"text": "Bam Adebayo's value is almost entirely in two non-box-score categories: on-ball defense against wings (he holds opponents to 0.79 PPP on isolation) and screen-setting quality (his screens are set 0.4 seconds longer on average than league average, creating more effective separation for shooters).", "label": "analysis"},

    # ── Additional REACTION examples ───────────────────────────────────────────
    {"text": "NOBODY TELL ME WHAT HAPPENED IN THE LAST 2 MINUTES I HAD TO LEAVE BUT I'M WATCHING THE REPLAY RIGHT NOW", "label": "reaction"},
    {"text": "I watched the Celtics game with my dad last night. He's been a fan for 50 years. Neither of us could believe what we were watching. Special memories.", "label": "reaction"},
    {"text": "That game 7 finish is going in the all-time great moments conversation. I will be talking about that shot for the rest of my life.", "label": "reaction"},
    {"text": "Woke up to the news this morning and I genuinely need a moment. Did not see this trade coming. At all. Processing.", "label": "reaction"},
    {"text": "I'm done watching sports. I mean it this time. I said it last year too but this time I really mean it. This team is going to put me in an early grave.", "label": "reaction"},
    {"text": "The roar in the arena when he hit that shot could be heard from outside the building. I was there. One of the greatest atmospheres I've ever experienced.", "label": "reaction"},
    {"text": "They're playing tonight and I can't watch because I'm working. Please nobody spoil it. I'm going home straight after and watching the replay.", "label": "reaction"},
    {"text": "Tatum in the fourth quarter tonight is just different. He's locked in. Whoever's guarding him right now is having a very bad night.", "label": "reaction"},
    {"text": "That comeback win should not have been possible. Down 20 with 6 minutes left and somehow. SOMEHOW. I was watching with my hands over my eyes.", "label": "reaction"},
    {"text": "SGA just went absolutely nuclear. Back to back to back buckets and the Thunder are up 12. Where did this come from?", "label": "reaction"},
    {"text": "The moment LeBron walked off the floor knowing it was the last game of his playoff run this year... I don't know. Gets to you a little.", "label": "reaction"},
    {"text": "MY TEAM IS IN THE CONFERENCE FINALS FOR THE FIRST TIME IN MY LIFETIME I CANNOT BELIEVE THIS IS HAPPENING", "label": "reaction"},
    {"text": "Going into halftime down 3 after playing their best first half of the season. This is the best we've looked all year. Let's see if they can hold it.", "label": "reaction"},
    {"text": "That possession with 11 seconds left is going to give me nightmares. Bad shot, bad rebounding, bad foul. We deserved to lose.", "label": "reaction"},
    {"text": "My heart rate during that last minute was probably not healthy. Sports are genuinely bad for you and I cannot stop watching.", "label": "reaction"},
    {"text": "The broadcast just cut away right before the big moment and I MISSED IT LIVE. Going to be rewatching this five times tonight.", "label": "reaction"},

    # ── More ANALYSIS to balance distribution ──────────────────────────────────
    {"text": "Why the Nuggets lose when Jokic is triple-teamed: Denver's other four players shoot 32.1% when three defenders are committed to Jokic. The offense needs at least one viable secondary creator to keep help honest. Without MPJ as a scoring threat, the math doesn't work.", "label": "analysis"},
    {"text": "Tatum's iso scoring efficiency (.98 PPP) is good but not elite — he ranks 28th among wings who take 4+ iso plays per game. His value comes from his off-ball movement and PnR usage, not from one-on-one plays. If teams can funnel him into isolation they contain his impact.", "label": "analysis"},
    {"text": "The reason Boston's defense is so effective is their rotation speed — they close out to the three-point line in an average of 0.8 seconds, which is 0.15 seconds faster than league average. That doesn't sound like much but it's the difference between a contested and an open look.", "label": "analysis"},
    {"text": "Embiid's playoff problems stem from one pattern: in elimination games, teams go under all screens against him, forcing him to prove he can make midrange jumpers under playoff intensity. His midrange percentage in elimination games (.38) is 8 points lower than in non-elimination games.", "label": "analysis"},
    {"text": "The Pacers' pace (103.5 possessions per game) is the fastest in the league, and it's structural, not accidental. Their entire roster was built around players who make decisions quickly — Haliburton averages 0.6 seconds to decision on PnR, compared to 1.1 for the league average point guard.", "label": "analysis"},
    {"text": "Dame's value to Portland over his career was obscured by a single number: the Blazers made the playoffs 8 of 9 years with him. That record understates his impact — their wins above replacement without him in those seasons would have been approximately -3.4, meaning they'd have been consistently lottery-bound.", "label": "analysis"},
    {"text": "Minnesota's playoff runs have all followed the same pattern: great regular season, first-round upset or early exit. The reason is their roster construction — they're excellent in halfcourt offense but rank in the bottom quarter in transition scoring. Playoff teams slow the game down and neutralize Minnesota's best attribute.", "label": "analysis"},
    {"text": "The drop in three-point volume from corner to above-the-break isn't just a preference issue — it reflects gravity. When a team's star drives hard to the rim, the help defense collapses, leaving corner shooters open. Above-the-break threes are typically off rotations or early in the shot clock, which are lower quality situations.", "label": "analysis"},
    {"text": "OKC's defensive identity is unusual: they switch everything, which most teams try to avoid because of size mismatches. It works because their entire roster (from Chet to SGA to Dort) can credibly guard anyone. The switch-everything scheme only functions when you have switchable defenders at all five positions.", "label": "analysis"},
    {"text": "Sabonis in Sacramento changed how teams play him over three seasons. In year 1, teams went under screens and dared him to shoot — he was at 31% from three. By year 3, he's at 38% on the same shot types, and now teams can no longer safely leave him. His development expanded the Kings' playbook.", "label": "analysis"},
    {"text": "Klay Thompson's career arc is the clearest illustration of ACL recovery timelines in recent basketball history. Players who return to full competition within 18 months of ACL reconstruction show a 34% higher re-injury rate in years 3-5 than players who take 24+ months. Klay's second ACL happened at almost exactly the 18-month mark.", "label": "analysis"},
    {"text": "The Lakers' core problem is the salary structure: they have three max or near-max players taking up 87% of their cap space with no mid-level exception remaining. This constrains roster construction to minimum-salary players who have to fill specific spacing and defensive roles. The margin for error is extremely small.", "label": "analysis"},
    {"text": "Mitchell Robinson's rebounding rate (20.4% defensive rebound rate) is historically elite, but it comes with a cost: he's so aggressive pursuing defensive rebounds that he's out of position for transition defense on long rebounds 38% of the time. Teams have specifically targeted Knicks transition defense off long misses against him.", "label": "analysis"},
    {"text": "The Clippers have been the most analytically-driven team in the league on shot selection for six years: they rank first in corner three rate, first in at-rim rate, and last in long mid-range rate. Their challenge is roster construction has never matched the analytics sophistication — they keep acquiring players who take the exact shots their system tries to avoid.", "label": "analysis"},
    {"text": "What's remarkable about the 2016 Warriors' 73-win season is that it was actually an underperformance relative to their metrics. Their expected wins based on point differential was 76.2 — meaning they went 73-9 despite underperforming their underlying efficiency numbers in close games.", "label": "analysis"},
    {"text": "The 3-and-D archetype emerged as a specific response to analytics: once teams understood the value of corner threes, they needed players who could credibly occupy corner spots without needing offensive creation. The economics followed — players who were athletic enough to guard wings but skilled enough to hit corner threes became highly paid.", "label": "analysis"},
    {"text": "Paolo Banchero's development curve is slightly ahead of historical comps for his draft class. His points per 36 improved from 18.7 to 22.3 to 24.8 across his first three seasons — that rate of improvement (roughly 3 points per 36 per year) is similar to early-career Carmelo Anthony and Kevin Durant.", "label": "analysis"},
    {"text": "What makes the current NBA pace sustainable is the rule changes around pace control. In the 2003-2008 era, pace dropped to 90 possessions per game and the product suffered — teams were grinding the shot clock intentionally. The rule changes that followed restored pace organically, not through arbitrary shot clock reduction.", "label": "analysis"},
    {"text": "The reason more teams don't run zone defense is not that it doesn't work — it's that you need specific personnel (a shot-blocker in the lane and a weak-side wing who can rotate quickly) and most rosters aren't built for it. Heat and Syracuse run zone because they systematically build for it. Most teams can't replicate that.", "label": "analysis"},
    {"text": "Duncan's career timing aligned perfectly with a rule set that valued his skills maximally. Post-handcheck rules and pace increase worked against him, but the elite PnR coverage allowed his hedging ability to function as a standalone defensive system for 19 seasons. He's the best argument for player-scheme alignment in NBA history.", "label": "analysis"},
    {"text": "Bradley Beal's efficiency problem is structural: he takes 22% of his shots from the long midrange (16-22 feet non-corner), which is the worst shot in basketball at .89 PPP. He's a high-volume scorer but his shot selection costs his team approximately 2.4 points per game compared to a player with the same athleticism but better shot distribution.", "label": "analysis"},

    # ── More REACTION examples ─────────────────────────────────────────────────
    {"text": "Playoff basketball in April is a completely different sport. The intensity of that game tonight felt like a different level. Regular season basketball cannot prepare you for this.", "label": "reaction"},
    {"text": "My dog started barking when I yelled at the TV during that last play. It's 11pm and I've probably woken up the neighbors. Not sorry.", "label": "reaction"},
    {"text": "I drove home from the bar after watching the game and I had to sit in my car for a few minutes before going inside. That result hit differently.", "label": "reaction"},
    {"text": "Checked my phone after dinner and saw the score notification. Did not need to see that. Thanks for ruining my evening.", "label": "reaction"},
    {"text": "THEY DID IT. FIRST TIME IN FRANCHISE HISTORY. I don't know what to do with myself right now.", "label": "reaction"},
    {"text": "That was the most stressful basketball game I've watched in years. Both teams played out of their minds. Standing ovation for everyone involved.", "label": "reaction"},
    {"text": "Bro just hit a 35-footer and immediately knew it was good. Didn't even look. Where does that confidence come from?", "label": "reaction"},
    {"text": "Turned off the game at the 2-minute mark because I couldn't watch anymore. Just checked the final score. Wish I'd stayed on.", "label": "reaction"},
    {"text": "The arena right now is ELECTRIC. Loudest I've ever heard it. The players can feel it.", "label": "reaction"},
    {"text": "I'm going to remember watching this series in 20 years. Pure basketball, both teams leaving everything on the floor. This is why we love this sport.", "label": "reaction"},
    {"text": "We were right there. RIGHT THERE. And then that call happened. I have nothing else to say tonight.", "label": "reaction"},
    {"text": "Watching this team fight back when everyone counted them out. I'm not crying. You're crying.", "label": "reaction"},
]


def strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def score_label(text: str) -> str:
    """Heuristic label for scraped posts (rough first pass)."""
    text_lower = text.lower()

    reaction_hits = sum([
        bool(re.search(r"\b(tonight|right now|this game|just happened|omg|omfg|lmao|wtf|holy|wow|insane|crazy|just saw)\b", text_lower)),
        bool(re.search(r"[!]{2,}", text)),
        bool(re.search(r"\b[A-Z]{4,}\b", text)),
        bool(re.search(r"^.{0,80}[!?]+$", text)),
        bool(re.search(r"\b(q[1-4]|game thread|post game|overtime|ot|halftime)\b", text_lower)),
    ])
    hot_take_hits = sum([
        bool(re.search(r"\b(overrated|underrated|most overrated|best ever|worst ever|goat|fraud|soft|crybaby)\b", text_lower)),
        bool(re.search(r"\b(jordan would|lebron would|could never|unpopular opinion|change my mind|hot take|actually|the truth)\b", text_lower)),
        bool(re.search(r"\b(nobody talks|everyone ignores|the media|era hopping|load management|scared)\b", text_lower)),
    ])
    analysis_hits = sum([
        bool(re.search(r"\d+\.?\d*\s*%", text)),
        bool(re.search(r"\bper 100|per 36|ts%|efg%|fg%|3p%|win share|bpm|vorp\b", text_lower)),
        bool(re.search(r"\b(historically|compared to|breakdown|data shows|in context|scheme|matchup|spacing)\b", text_lower)),
        bool(re.search(r"\bsince \d{4}|\bin the last \d+ year\b", text_lower)),
    ])

    if reaction_hits > hot_take_hits and reaction_hits > analysis_hits:
        return "reaction"
    if analysis_hits > reaction_hits and analysis_hits > hot_take_hits:
        return "analysis"
    if hot_take_hits > 0:
        return "hot_take"
    return "hot_take"  # default for news-style titles


def main():
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    rows = []

    # 1. Load scraped posts
    raw_path = data_dir / "raw_posts.csv"
    scraped_count = 0
    if raw_path.exists():
        with open(raw_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                text = row.get("text", "").strip()
                if not text or len(text) < 15:
                    continue
                label = score_label(text)
                rows.append({
                    "text": text[:512],
                    "label": label,
                    "notes": "scraped from r/nba RSS; auto-labeled — NEEDS MANUAL REVIEW",
                })
                scraped_count += 1
    print(f"Scraped posts loaded: {scraped_count}")

    # 2. Add curated examples
    for ex in CURATED:
        rows.append({
            "text": ex["text"],
            "label": ex["label"],
            "notes": "curated example — label confirmed",
        })
    print(f"Curated examples added: {len(CURATED)}")
    print(f"Total dataset size: {len(rows)}")

    # Label distribution
    from collections import Counter
    dist = Counter(r["label"] for r in rows)
    print("\nLabel distribution:")
    for lbl, cnt in sorted(dist.items()):
        print(f"  {lbl}: {cnt} ({cnt/len(rows)*100:.1f}%)")

    # Save
    out_path = data_dir / "nba_dataset.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "label", "notes"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nSaved {len(rows)} rows -> {out_path}")


if __name__ == "__main__":
    main()
