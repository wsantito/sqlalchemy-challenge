from flask import Flask, jsonify
import datetime as dt
import sqlalchemy
import pandas as pd
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, inspect
from datetime import datetime, date, timedelta
from matplotlib.dates import DateFormatter

engine = create_engine("sqlite:///hawaii.sqlite")

# Declare a Base using `automap_base()`
Base = automap_base()
#Base.metadata.create_all(engine)
Base.prepare(engine, reflect=True)
#Base
#inspector = inspect(engine)
#print(inspector.get_table_names())
Measurement = Base.classes.measurement
Station = Base.classes.station
session = Session(bind=engine)


#Measurement = session.query(Measurement).first()


#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Flask Routes
#################################################

@app.route("/")
def welcome():
    return (
        f"Welcome to the weather API!<br/>"
        f"*** Our data base is from 2010-01-01 to 2017-08-23 ***<br/>"
        f"--All records of precipitation by date<br/>"
        f"/api/v1.0/precipitation<br/>"
        F"--List of all the stations<br/>"
        f"/api/v1.0/stations<br/>"
        f"--Temperature observations (TOBS) for the previous year of the station with more observations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"--For a single day, Use format YYYY-MM-DD<br/>"
            f"/api/v1.0/(Date)<br/>"
        f"--For data between two dates, Use format YYYY-MM-DD/YYYY-MM-DD<br/>"
            f"/api/v1.0/(start date/end date)<br/>"
    )

"""TODO: Handle API route with variable path to allow getting info
for a specific character based on their 'superhero' name """

#Convert the query results to a dictionary using date as the key and prcp as the value.
#Return the JSON representation of your dictionary.


@app.route("/api/v1.0/precipitation")
def precipitation():

    query_1year = dt.date.today() - dt.timedelta(days=365)

    Query1 = session.query(Measurement.date, Measurement.prcp).\
    filter(Measurement.date < query_1year).\
    order_by(Measurement.date).all() 

    precipitation = {date:prcp for date,prcp in Query1}
    #__dict__

    return jsonify(precipitation)

#Return a JSON list of stations from the dataset.
   
@app.route("/api/v1.0/stations")
def Stations():

    QueryS = session.query(Station.station, Station.name)
    station = {station:name for station,name in QueryS}
    return jsonify(station)

#Query the dates and temperature observations of the most active station for the last year of data.
#Return a JSON list of temperature observations (TOBS) for the previous year.

@app.route("/api/v1.0/tobs")
def Tobs():

    QueryM = session.query(Measurement.id, Measurement.station, Measurement.date, Measurement.prcp, Measurement.tobs)
    QueryM = pd.DataFrame(QueryM)
    QueryMC = QueryM.dropna()

    StationTempCount = QueryMC.groupby(["station"])[["tobs"]].count()
    StationTempCount = StationTempCount.rename(columns={"tobs": "Temp Counts"})
    TopTemp = StationTempCount[StationTempCount['Temp Counts']==StationTempCount['Temp Counts'].max()]
    TopTempStat = TopTemp.index.values[-1]

    query_1year = dt.date.today() - dt.timedelta(days=365)

    Query5 = session.query(Measurement.date, Measurement.station, Measurement.tobs).\
    filter(Measurement.date < query_1year).\
    filter(Measurement.station == TopTempStat).\
    order_by(Measurement.date).all()

    resultado = {
        "Resultado" : Query5,
        "Mensaje" : "la peticion fue exitosa"
    }

    return jsonify(resultado)

@app.route("/api/v1.0/<start>")
def Travel1(start):

    #datetime.strptime(date_string, format)
    start = start.format('datetime64[ns]')
    
    qry2 = session.query(func.max(Measurement.tobs).filter(Measurement.date == start).label("Max_Temp"), 
    func.min(Measurement.tobs).filter(Measurement.date == start).label("Min_Temp"),
    func.avg(Measurement.tobs).filter(Measurement.date == start).label("Avg_Temp"),
    )
    res = qry2.one()
    max = res.Max_Temp
    min = res.Min_Temp
    avg = res.Avg_Temp
    
    Temperatures = [
    {"Date":start},
    {"Min": min},
    {"Avg": avg},
    {"Max": max}
    ]

    return jsonify(Temperatures)

@app.route("/api/v1.0/<SD>/<ED>")
def daily_normals(SD,ED):
    
    SD = date.fromisoformat(SD)
    ED = date.fromisoformat(ED)

    numdays =  ED - SD

    # Use the start and end date to create a range of dates
    dateList = []
    MinT = []
    MaxT = []
    AvgT = []

    for x in range(0, numdays.days):
        NewDate = (ED - dt.timedelta(days = x))

        sel = [func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)]
        RES = session.query(*sel).filter(Measurement.date == NewDate).all()

        dateList.append(NewDate)
        MinT.append(RES[0][0])
        AvgT.append(RES[0][1])
        MaxT.append(RES[0][2])
    

    Datesdf = pd.DataFrame(dateList)
    Datesdf = Datesdf.rename(columns={0: "Dates"})
    Datesdf["MinT"]= pd.DataFrame(MinT)
    Datesdf["AvgT"] = pd.DataFrame(AvgT)
    Datesdf["MaxT"] = pd.DataFrame(MaxT)

    Datesdf_dict = Datesdf.to_records().tolist()

    return jsonify(Datesdf_dict)


if __name__ == "__main__":
    app.run(debug=True)
