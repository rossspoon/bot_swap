
import pandas as pd

print("Preprocessing participants")

TEMP_DIR = 'Preproc/temp'
part_data = pd.read_csv(f'{TEMP_DIR}/normalized_part.csv')
survey_data = pd.read_csv(f'{TEMP_DIR}/temp_surveys.csv').set_index('part_label')
group_data = pd.read_csv(f'{TEMP_DIR}/normalized_group.csv')
player_data = pd.read_csv(f'{TEMP_DIR}/normalized_player.csv')
sess_data = pd.read_csv(f'{TEMP_DIR}/normalized_session.csv')
order_data = pd.read_csv(f'{TEMP_DIR}/preproc_orders.csv')
landing_data = pd.read_csv(f'{TEMP_DIR}/normalized_landing.csv').set_index('part_label')
payment_data = pd.read_csv(f'{TEMP_DIR}/normalized_payment.csv').set_index('part_label')

cols_to_drop = ['_is_bot', '_max_page_index', '_index_in_pages', '_current_page_name', '_current_app_name', 'visited', 'mturk_worker_id', 'mturk_assignment_id']

print("Removing unnecessary columns")
part_data.drop(cols_to_drop, axis=1, inplace=True)

print("Joining survey data")
part_with_survey = part_data.join(survey_data, on='part_label')
#%%
print("Joining instruction data")
landing_data.drop(['session', 'id_in_group'], axis=1, inplace=True)
part_final = part_with_survey.join(landing_data, on='part_label')
#%%

################
## GRADED Items
################
def grade_column(df, column, answer, fill=0):
    score_col = f"{column}_score"
    df[score_col] = (df[column] == answer).astype(int)
    df.loc[df[column].isna(), score_col] = fill
    df[score_col] = df[score_col].astype(int)

# Grade the quiz
print("Grading quiz")
grade_column(part_final, 'quiz_1_init', 2)
grade_column(part_final, 'quiz_2_init', 2)
grade_column(part_final, 'quiz_3_init', 210)
grade_column(part_final, 'quiz_4_init', 110)
grade_column(part_final, 'quiz_5_init', 56)
quiz_score_cols = ['quiz_1_init_score', 'quiz_2_init_score', 'quiz_3_init_score', 'quiz_4_init_score', 'quiz_5_init_score']
part_final['quiz_grade'] = part_final[quiz_score_cols].sum(axis=1)
quiz_cols = ['quiz_1_init', 'quiz_2_init', 'quiz_3_init', 'quiz_4_init', 'quiz_5_init']
missing_all = part_final[quiz_cols].isna().all(axis=1)
part_final['took_quiz'] = (~missing_all).astype(int)


####
# Calculate Payouts
####
# TODO:   Remove this and place the payouts in the experiment sensibly.
print("Joining Payouts")

cols=['clicked_button', 'market_bonus', 'forecast_bonus', 'risk_bonus', 'total_bonus', 'showup', 'total_payment']
part_final = part_final.join(payment_data[cols], on='part_label')


#########
##  Number of Trades
#########
attempted_trades = order_data.groupby('part_label').type.count()
attempted_trades.name = 'attempted_trades'
part_final = part_final.join(attempted_trades, on='part_label')

executed_trades = order_data[order_data.quantity_final > 0].groupby('part_label').type.count()
executed_trades.name = 'executed_trades'
part_final = part_final.join(executed_trades, on='part_label')



#%% md

#%%
# b = ['quiz_1', 'quiz_2', 'quiz_3', 'quiz_4', 'five_years', 'one_year', 'stock_safer', 'bat_and_ball', 'widgets', 'lilies_on_lake']
# cols = []
# for c in b:
#     cols.append(c)
#     cols.append(f"{c}_score")
# part_final[cols]
#%%
# Write out to disk
print("Writing to disk")
part_final.to_csv(f'{TEMP_DIR}/preproc_participant.csv', index=False)