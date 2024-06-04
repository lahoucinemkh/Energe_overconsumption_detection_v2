from anomalyDetector import app
import os
import pandas as pd
from flask import render_template, redirect, url_for, flash, send_file, request
from anomalyDetector import logger
from datetime import datetime
from anomalyDetector.pipeline.stage_01_data_ingestion import DataIngestionTrainingPipeline
from anomalyDetector.pipeline.stage_02_base_model import BaseModelTrainingPipeline
from anomalyDetector.pipeline.stage_03_data_availability import DataAvailabilityTrainingPipeline
from anomalyDetector.pipeline.stage_04_anomaly_occurrence import AnomalyOccurrenceTrainingPipeline
from anomalyDetector.components.anomalies_download import anomaliesDownload
from anomalyDetector.components.anomalies_upload import AnomaliesUpload
from anomalyDetector.db.models import User, Site, Anomaly
from anomalyDetector.forms import RegisterForm, LoginForm, DataIngestionForm, DataAvailabilityForm, AnomalyOccurrenceForm, BaseModelForm, AnomalyEditForm, SiteSelectionForm, DownloadForm, UpdateForm
from anomalyDetector.db.db import session
from flask_login import login_user, logout_user, login_required
from sqlalchemy.orm.exc import NoResultFound


@app.route('/')
@app.route('/home')
def home_page():
    return render_template('home.html')


@app.route('/register', methods=['GET', 'POST'])
def register_page():
    form = RegisterForm()
    if form.validate_on_submit():
        user_to_create = User(email_address=form.email_address.data,
                              password=form.password1.data)
        session.add(user_to_create)
        session.commit()
        login_user(user_to_create)
        flash(f"Account created successfully! You are now logged in as {user_to_create.email_address}", category='success')
        return redirect(url_for('home_page'))
    if form.errors != {}: #If there are not errors from the validations
        for err_msg in form.errors.values():
            flash(f'There was an error with creating a user: {err_msg}', category='danger')

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    form = LoginForm()
    if form.validate_on_submit():
        attempted_user = session.query(User).filter(User.email_address == form.email_address.data).first()
        if attempted_user and attempted_user.check_password_correction(
                attempted_password=form.password.data
        ):
            login_user(attempted_user)
            flash(f'Success! You are logged in as: {attempted_user.email_address}', category='success')
            return redirect(url_for('home_page'))
        else:
            flash('Username and password are not match! Please try again', category='danger')

    return render_template('login.html', form=form)  


@app.route('/logout')
def logout_page():
    logout_user()
    flash("You have been logged out!", category='info')
    return redirect(url_for("home_page"))  
     


@app.route('/manage_anomalies', methods=['GET', 'POST'])
@login_required
def manage_anomalies_page():
    site_form = SiteSelectionForm()
    anomaly_form = AnomalyEditForm()
    
    # Populate site codes for selection
    sites = session.query(Site).all()
    site_form.site_code.choices = [(site.id, site.site_code) for site in sites]

    anomalies = []
    
    if site_form.validate_on_submit():
        site_id = site_form.site_code.data
        start_date = site_form.start_date.data
        end_date = site_form.end_date.data

        anomalies = session.query(Anomaly).filter(
            Anomaly.site_id == site_id,
            Anomaly.start_date >= start_date,
            Anomaly.end_date <= end_date
        ).all()
    
    if anomaly_form.validate_on_submit():
        if anomaly_form.submit_edit.data:
            anomaly_id = anomaly_form.id.data
            try:
                anomaly = session.query(Anomaly).filter(Anomaly.id == anomaly_id).one()
                anomaly.start_date = anomaly_form.start_date.data
                anomaly.end_date = anomaly_form.end_date.data
                anomaly.consumption_value = anomaly_form.consumption_value.data
                anomaly.nbr_hour_consumption = anomaly_form.nbr_hour_consumption.data
                anomaly.nbr_days_consumption = anomaly_form.nbr_days_consumption.data
                anomaly.start_time = anomaly_form.start_time.data
                anomaly.impact_consumption = anomaly_form.impact_consumption.data
                anomaly.period_type = anomaly_form.period_type.data
                anomaly.comments = anomaly_form.comments.data
                session.commit()
                flash('Anomaly updated successfully!', 'success')
            except NoResultFound:
                flash('Anomaly not found!', 'danger')
        elif anomaly_form.submit_delete.data:
            anomaly_id = anomaly_form.id.data
            try:
                anomaly = session.query(Anomaly).filter(Anomaly.id == anomaly_id).one()
                session.delete(anomaly)
                session.commit()
                flash('Anomaly deleted successfully!', 'success')
            except NoResultFound:
                flash('Anomaly not found!', 'danger')
        elif anomaly_form.submit_add.data:
            new_anomaly = Anomaly(
                site_id=site_form.site_code.data,
                start_date=anomaly_form.start_date.data,
                end_date=anomaly_form.end_date.data,
                consumption_value=anomaly_form.consumption_value.data,
                nbr_hour_consumption=anomaly_form.nbr_hour_consumption.data,
                nbr_days_consumption=anomaly_form.nbr_days_consumption.data,
                start_time=anomaly_form.start_time.data,
                impact_consumption=anomaly_form.impact_consumption.data,
                period_type=anomaly_form.period_type.data,
                comments=anomaly_form.comments.data
            )
            session.add(new_anomaly)
            session.commit()
            flash('Anomaly added successfully!', 'success')
        elif anomaly_form.submit_validate.data:
            # Handle validation logic if needed
            pass

    return render_template('manage_anomalies.html', site_form=site_form, anomaly_form=anomaly_form, anomalies=anomalies)     


@app.route('/detector', methods=['GET', 'POST'])
@login_required
def detector_page():
    DataIngestion = DataIngestionForm()
    DataAvailability = DataAvailabilityForm()
    AnomalyOccurrence = AnomalyOccurrenceForm()
    BaseModel = BaseModelForm()
    Download = DownloadForm()
    AnomalyUpdate = UpdateForm()

    if request.method == 'POST':
        form_type = request.form.get('form_type')

        if form_type == 'data_ingestion' and DataIngestion.validate_on_submit():
            handle_data_ingestion(DataIngestion)
            return redirect(url_for('detector_page'))

        if form_type == 'data_availability' and DataAvailability.validate_on_submit():
            handle_data_availability(DataAvailability)
            return redirect(url_for('detector_page'))
   

        if form_type == 'base_model' and BaseModel.validate_on_submit():
            handle_base_model(BaseModel)
            return redirect(url_for('detector_page'))

        if form_type == 'download' and Download.validate_on_submit():
            handle_download(Download)
            return redirect(url_for('detector_page'))

        if form_type == 'anomaly_update' and AnomalyUpdate.validate_on_submit():
            handle_anomaly_update(AnomalyUpdate)
            return redirect(url_for('detector_page'))

        if form_type == 'anomaly_occurrence' and AnomalyOccurrence.validate_on_submit():
            handle_anomaly_occurrence(AnomalyOccurrence)
            return redirect(url_for('detector_page'))         

    return render_template('detector.html', DataIngestion=DataIngestion, DataAvailability=DataAvailability, BaseModel=BaseModel, Download=Download, AnomalyUpdate=AnomalyUpdate, AnomalyOccurrence=AnomalyOccurrence)

def handle_data_ingestion(form):
    sites_from_db = session.query(Site).all()
    id_list, codeRef_list, siteRef_list, brancheRef_list = [], [], [], []

    start = form.start_date.data
    end = form.end_date.data

    for site in sites_from_db:
        codeRef_list.append(site.site_code)
        siteRef_list.append(site.name)
        brancheRef_list.append(site.branch)
        id_list.append(site.id)

    STAGE_NAME = "Data Ingestion"
    try:
        logger.info(f">>>>>> stage {STAGE_NAME} started <<<<<<")
        data_ingestion = DataIngestionTrainingPipeline(start, end, id_list, codeRef_list, siteRef_list, brancheRef_list)
        data_ingestion.main()
        logger.info(f">>>>>> stage {STAGE_NAME} completed <<<<<<\n\nx==========x")
        flash(f"Stage of data ingestion passed successfully!", category='success')
    except Exception as e:
        logger.exception(e)
        flash(f"An error occurred during data ingestion: {e}", category='danger')

def handle_data_availability(form):
    start = form.start_date.data
    end = form.end_date.data

    STAGE_NAME = "Data Availability"
    try:
        logger.info(f">>>>>> stage {STAGE_NAME} started <<<<<<")
        data_availability = DataAvailabilityTrainingPipeline(start, end)
        data_availability.main()
        logger.info(f">>>>>> stage {STAGE_NAME} completed <<<<<<\n\nx==========x")
        flash(f"Stage of data availability passed successfully!", category='success')
    except Exception as e:
        logger.exception(e)
        flash(f"An error occurred during data availability check: {e}", category='danger')

def handle_base_model(form):
    start = datetime.combine(form.start_date.data, datetime.min.time())
    end = datetime.combine(form.end_date.data, datetime.min.time())

    sites_from_db = session.query(Site).all()
    id_list, codeRef_list, fer_list, ouv_list, tal_list, marg, dfer_list, douv_list = [], [], [], [], [], [], [], []

    for site in sites_from_db:
        id_list.append(site.id)
        codeRef_list.append(site.site_code)
        fer_list.append(site.closing_hour_week)
        ouv_list.append(site.opening_hour_week)
        tal_list.append(site.winter_threshold)
        marg.append(site.margin)
        dfer_list.append(site.closing_hour_sun)
        douv_list.append(site.opening_hour_sun)

    for i in range(len(codeRef_list)):
        site_code = codeRef_list[i]
        opening_hour_week = ouv_list[i]
        closing_hour_week = fer_list[i]
        closing_hour_sun = dfer_list[i]
        opening_hour_sun = douv_list[i]
        threshold = tal_list[i]
        margin = marg[i]
        id = id_list[i]

        STAGE_NAME = "base model"
        try:
            logger.info(f">>>>>> stage {STAGE_NAME} started <<<<<<")
            prepare_base_model = BaseModelTrainingPipeline(id, start, end, site_code, closing_hour_week, opening_hour_week, threshold, margin, closing_hour_sun, opening_hour_sun)
            prepare_base_model.main()
            logger.info(f">>>>>> stage {STAGE_NAME} completed <<<<<<\n\nx==========x")
            flash(f"Stage of anomalies detection passed successfully!", category='success')
        except Exception as e:
            logger.exception(e)
            flash(f"An error occurred during anomalies detection: {e}", category='danger')

def handle_download(form):
    start = form.start_date.data
    end = form.end_date.data

    # Construire un chemin absolu pour le fichier de sortie
    base_dir = os.path.abspath(os.path.dirname(__file__))
    output_file = os.path.join(base_dir, '..', 'suivi_auto.xlsx')

    STAGE_NAME = "Anomalies Download"
    try:
        logger.info(f">>>>>> stage {STAGE_NAME} started <<<<<<")
        anomalies_download = anomaliesDownload(start, end)
        anomalies_download.getAnomalies(output_file)
        logger.info(f">>>>>> stage {STAGE_NAME} completed <<<<<<\n\nx==========x")
        flash(f"Stage of anomalies download passed successfully!", category='success')
        return send_file(output_file, as_attachment=True)
    except Exception as e:
        logger.exception(e)
        flash(f"An error occurred during anomalies download: {e}", category='danger')

def handle_anomaly_update(form):
    start_date = form.start_date.data
    end_date = form.end_date.data
    file = form.file.data

    
    df = pd.read_excel(file,  sheet_name='Feuil2', header=0, skiprows=0)

    STAGE_NAME = "Anomalies Update"
    try:
        logger.info(f">>>>>> stage {STAGE_NAME} started <<<<<<")
        anomaly_upload = AnomaliesUpload(start_date, end_date, df)
        anomaly_upload.delete_existing_anomalies()
        anomaly_upload.insert_validated_anomalies()
        logger.info(f">>>>>> stage {STAGE_NAME} started <<<<<<")
        flash("Anomalies updated successfully!", category='success')        
    except Exception as e:
        logger.exception(e)
        flash(f"An error occurred during anomalies update: {e}", category='danger')

def handle_anomaly_occurrence(form):
    start = form.start_date.data
    end = form.end_date.data

    STAGE_NAME = "anomaly occurrence"
    try: 
        logger.info(f"*******************")
        logger.info(f">>>>>> stage {STAGE_NAME} started <<<<<<")
        prepare_anomaly_occurrence = AnomalyOccurrenceTrainingPipeline(start, end)
        prepare_anomaly_occurrence.main()
        logger.info(f">>>>>> stage {STAGE_NAME} completed <<<<<<\n\nx==========x")
        flash("Anomaly occurrence check passed successfully!", category='success')    
    except Exception as e:
        logger.exception(e)
        flash(f"An error occurred during anomaly occurrence check: {e}", category='danger')

    