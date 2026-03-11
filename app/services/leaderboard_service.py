"""
FR6 — Leaderboard service.
The most complex service: token calculation, upsert leaderboard entries,
weekly snapshot-and-reset, Monday bonus awards.
"""
# TODO: implement the following functions

# calculate_tokens(db, activity_type, hours_worked, is_sustainability) -> Decimal
#   - Query TokenRule WHERE rule_type=activity_type AND is_active=True
#   - Apply hours multiplier from rule.condition_details
#   - Apply sustainability bonus multiplier if is_sustainability=True
#   - Return calculated token amount

# update_leaderboard_entry(db, employee_id, org_id, score_delta, token_delta) -> None
#   - Find or create the open LeaderboardSnapshot for org_id (current ISO week)
#   - PostgreSQL upsert:
#       INSERT INTO leaderboard_entries (leaderboard_id, employee_id, score, total_tokens)
#       VALUES (...)
#       ON CONFLICT (leaderboard_id, employee_id)
#       DO UPDATE SET score = score + score_delta, total_tokens = total_tokens + token_delta
#   - Use sqlalchemy.dialects.postgresql insert().on_conflict_do_update()

# get_leaderboard(db, org_id, week_start=None) -> list[LeaderboardEntry]
#   - Get open snapshot for org (or snapshot by week_start if provided)
#   - Return entries ordered by score DESC
#   - Compute rank_position in Python (or use SQL ROW_NUMBER())

# reset_leaderboard(db, org_id) -> LeaderboardSnapshot
#   FR-6.6: Called by Sunday 23:59 cron job.
#   1. Get current open LeaderboardSnapshot for org
#   2. Set snapshot.status = 'closed', snapshot.reset_date = today
#   3. Create new open LeaderboardSnapshot for next week (period_start = next Monday)
#   4. Write audit log: "leaderboard.reset" with snapshot.id
#   5. Return closed snapshot (used by award_monday_bonus)

# award_monday_bonus(db, org_id, top_n=3) -> None
#   FR-6.7: Called by Monday 00:05 cron job.
#   1. Get last closed LeaderboardSnapshot for org
#   2. Get top_n entries by score
#   3. For each winner:
#      a. Call Omar's wallet_service.credit_tokens(employee_id, bonus_amount, "leaderboard_bonus")
#      b. Update leaderboard_entry.bonus_tokens += bonus_amount, bonus_paid=True
#      c. Call notification_service.notify_leaderboard_rank(db, employee_id, rank, week)
#      d. Write audit log: "tokens.bonus_awarded"
#   Note: bonus_amount comes from TokenRule WHERE rule_type='leaderboard_bonus'
