import pandas as pd
from jinja2 import Template


DATA_DIR = 'Presentation/input/data'
TEMPLATE_DIR = 'Presentation/template'
TEX_DIR = 'Presentation/temp/'


session_data = pd.read_csv(f'{DATA_DIR}/session.csv')
part_data = pd.read_csv(f'{DATA_DIR}/participant.csv').set_index('session')

sessions = list(session_data.session)



with open(f'{TEMPLATE_DIR}/session_summary_template.tex', 'r') as f:
    template_str = f.read()


for s in sessions:
    parts_for_sess = part_data.loc[s].drop_duplicates('part_label')
    
    parts_dict = parts_for_sess.set_index('part_label').to_dict(orient='index')
    
    sess_label = session_data[session_data.session == s].label
    
    # Render the latex with the player data
    t = Template(template_str)
    tex = t.render(sess=s, sess_label=sess_label, participants=parts_for_sess.part_label, part_data=parts_dict)

    
    with open(f'{TEX_DIR}/session_summary_{s}.tex', 'w') as f:
        f.write(tex)