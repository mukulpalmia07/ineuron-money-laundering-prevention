import streamlit as st
import pandas as pd
from dataclasses import dataclass
from pathlib import Path
from src.main import predict, start_model_training

# --- Force Reset Session State on Refresh --- #
for key in list(st.session_state.keys()):
    del st.session_state[key]

# --- Page Configuration --- #
st.set_page_config(
    page_title='Money Laundering Prevention',
    page_icon='💰',
    layout='wide',
    initial_sidebar_state='expanded',
)

# --- Custom Styling --- #
st.markdown(
    """
    <style>
        .main-title { text-align: center; color: #007FFF; }
        .header { display: flex; justify-content: center; align-items: center; }
        .header img { height: 70px; }
        .stButton button { width: 100%; }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Header --- #
st.markdown('<div class="header"><img src="https://ineuron.ai/images/ineuron-logo.png" alt="Logo"></div>', unsafe_allow_html=True)
st.markdown('<h2 class="main-title">Money Laundering Prevention System</h2>', unsafe_allow_html=True)

@dataclass
class BaseDF:
    sourceid: int
    destinationid: int
    amountofmoney: int
    month: int
    typeofaction: str
    typeoffraud: str

    def __iter__(self):
        yield 'sourceid', self.sourceid
        yield 'destinationid', self.destinationid
        yield 'amountofmoney', self.amountofmoney
        yield 'month', self.month
        yield 'typeofaction', self.typeofaction
        yield 'typeoffraud', self.typeoffraud

# --- Sidebar: Select Prediction Type --- #
st.sidebar.title('Navigation')
prediction_type = st.sidebar.radio('Select Prediction Type', ['Prediction from Form', 'Batch Prediction'])

# --- Ensure Model Training is Reset on Refresh --- #
st.session_state.model_trained = False

# --- Train Model Section --- #
def train_model():
    """Triggers model training and updates session state."""
    try:
        start_model_training()
    except FileNotFoundError:
        st.error('Training data not found. Ensure "data/base_data.csv" exists.', icon='🚨')
        return
    st.session_state.model_trained = True
    st.success('Model training completed! 🎉')
    st.balloons()

if st.sidebar.button('Train Model', use_container_width=True):
    with st.spinner('Training model...'):
        train_model()

# --- Main Section: Form or Batch Prediction --- #
base = None
msg = st.empty()

if prediction_type == 'Prediction from Form':
    with st.form('form_prediction'):
        col1, col2 = st.columns(2)
        
        with col1:
            sourceid = st.number_input('Source ID', min_value=1, value=44604, step=1, format='%d')
            amountofmoney = st.number_input('Amount of Money', min_value=1, value=59999, step=1, format='%d')
            typeofaction = st.selectbox('Type of Action', ['cash-in', 'transfer'])
        
        with col2:
            destinationid = st.number_input('Destination ID', min_value=1, value=7869, step=1, format='%d')
            month = st.number_input('Transaction Month', min_value=1, max_value=12, value=3, step=1, format='%d')
            typeoffraud = st.selectbox('Type of Fraud', ['type1', 'type2', 'type3', 'none'])

        if st.form_submit_button('Predict'):
            base = BaseDF(sourceid, destinationid, amountofmoney, month, typeofaction, typeoffraud)

else:  # Batch Prediction
    with st.form('batch_prediction'):
        upload = st.file_uploader('Upload CSV file for Batch Prediction', type='csv')
        
        if st.form_submit_button('Predict Batch'):
            if upload is None:
                st.error('Please upload a CSV file.', icon='🚨')
            else:
                try:
                    base = pd.read_csv(upload)
                except Exception as e:
                    st.error(f'Failed to read the CSV file. Error: {str(e)}')
                    base = None

# --- Processing Predictions --- #
if base is not None:
    if isinstance(base, BaseDF):
        df = pd.DataFrame([dict(base)])
        try:
            _, prediction = predict(df)
        except FileNotFoundError:
            msg.error('Model is not trained yet. Please train the model first.', icon='🔥')
        else:
            result, color = ('Fraud', 'red') if prediction == 1 else ('Not Fraud', 'green')
            st.subheader(f':{color}[The transaction is {result}.]')
    elif isinstance(base, pd.DataFrame):
        try:
            pred_df, _ = predict(base)
        except FileNotFoundError:
            msg.error('Model is not trained yet. Please train the model first.', icon='🤖')
        else:
            st.balloons()
            msg.success('Download the predicted data file.')
            st.download_button(
                label='Download Prediction Results',
                data=pred_df.to_csv(index=False),
                file_name='Money-Laundering-Prediction.csv',
                mime='text/csv',
                use_container_width=True,
            )
else:
    st.markdown('<h3 style="text-align:center">Submit the form to get predictions.</h3>', unsafe_allow_html=True)
