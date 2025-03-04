import streamlit as st
import pandas as pd
from dataclasses import dataclass
from pathlib import Path
from src.main import predict, start_model_training

# --- Page Configuration --- #
st.set_page_config(
    page_title='Money Laundering Prevention',
    page_icon='💰',
    layout='wide',
    initial_sidebar_state='expanded',
)

# --- Sidebar Navigation --- #
st.sidebar.title('Navigation')
prediction_type = st.sidebar.radio('Select Prediction Type', ['Prediction from Form', 'Batch Prediction'])

# --- Initialize Session State for Model --- #
if "model_trained" not in st.session_state:
    st.session_state.model_trained = False  # Model is not trained initially
    st.session_state.trained_model = None  # Ensure no model is stored

def train_model():
    """Triggers model training, removes old model if exists, and updates session state."""
    if st.session_state.model_trained:
        st.warning("Removing previously trained model...")  # Notify user
        st.session_state.trained_model = None  # Remove existing model

    with st.spinner("Training model..."):
        try:
            model = start_model_training()  # Train the model
        except Exception:
            model = start_model_training(Path('data/base_data.csv'))
        
        st.session_state.trained_model = model  # Store model in session state
        st.session_state.model_trained = True  # Mark as trained
        st.success("Model training completed! 🎉")
        st.balloons()

# --- Train Model Button --- #
if st.sidebar.button("Train Model", use_container_width=True):
    train_model()

# --- Prediction Logic --- #
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
                base = pd.read_csv(upload)

# --- Processing Predictions --- #
if base is not None:
    if isinstance(base, BaseDF):
        df = pd.DataFrame([dict(base)])
        if st.session_state.trained_model is None:
            msg.error('Model is not trained yet. Please train the model first.', icon='🔥')
        else:
            _, prediction = predict(df)
            result, color = ('Fraud', 'red') if prediction == 1 else ('Not Fraud', 'green')
            st.subheader(f':{color}[The transaction is {result}.]')
    elif isinstance(base, pd.DataFrame):
        if st.session_state.trained_model is None:
            msg.error('Model is not trained yet. Please train the model first.', icon='🤖')
        else:
            pred_df, _ = predict(base)
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
