import os
from flask import Flask, app, jsonify, request, render_template, redirect, session, url_for
from google.cloud import storage
import mysql.connector
from datetime import datetime as dt
import re

#tạo một đối tượng của lớp
app=Flask(__name__)

#hàm kết nối tới database
def connect_to_database():
    return mysql.connector.connect(
        host="localhost", user="root", password="", database="cnpm"
    )

@app.route("/")
def index():
    return redirect(url_for("home"))

# màn hình chính của trang web index
@app.route("/index.html", methods=["GET","POST"])
def home():
    mydb=connect_to_database()
    mycursor=mydb.cursor()
    sql_get_room_in_index="(SELECT * FROM phong WHERE LoaiPhong = 'A' ORDER BY RAND() LIMIT 1) UNION (SELECT * FROM phong WHERE LoaiPhong = 'B' ORDER BY RAND() LIMIT 1) UNION ( SELECT * FROM phong WHERE LoaiPhong = 'C' ORDER BY RAND() LIMIT 1 ) ORDER BY RAND() LIMIT 3"
    mycursor.execute(sql_get_room_in_index)
    result_get_room_in_index=mycursor.fetchall()
    mycursor.close()
    mydb.close()
    return render_template("user/index.html", data_result_index=result_get_room_in_index)

#form điền thông tin thuê phòng
@app.route("/rent_room/<item_id>", methods=["GET","POST"])
def rent_room(item_id):
    mydb=connect_to_database() #hàm kết nối databse  
    mycursor=mydb.cursor()
    sql_receive_data="SELECT * FROM phong WHERE stt=%s" # hàm truy vấn dữ liệu 
    val_receive_data=(item_id,)
    mycursor.execute(sql_receive_data,val_receive_data)
    result_receive_data=mycursor.fetchone()
    money_per_night=result_receive_data[4] # lấy thong tin tiền từ phòng 
    print("moneypernight: ", money_per_night) # in thông tin tiền
    print("kết quả là: ", str(result_receive_data)) # in thong tin kết quả lấy toàn bị dữ liệu
    if request.method=="POST":
        name=request.form["name"]
        phone=request.form["phone"]
        email=request.form["email"]
        checkin_in=request.form["checkin_in"]
        
        #dùng strptime để chuyển chuỗi checkin-in thành datetime
        checkin_in_strptime=dt.strptime(checkin_in,"%d %B, %Y")
        # print("checkin_in_strptime",checkin_in_strptime) 
        
        #dùng strftime để chuyển thành chuỗi datetime
        checkin_in_strftime=checkin_in_strptime.strftime("%Y-%m-%d")

        checkin_out=request.form["checkin_out"]

        #dùng strptime để chuyển chuỗi checkin-out thành datetime
        checkin_out_strptime=dt.strptime(checkin_out,"%d %B, %Y")
        
        #dùng strftime để chuyển thành chuỗi datetime của checkin_out
        checkin_out_strftime=checkin_out_strptime.strftime("%Y-%m-%d") 
          
        adults=request.form["adults"]
        children=request.form["children"]
        message=request.form["message"]
        
    return render_template("user/rent_room.html", data_receive=result_receive_data)


# điều hướng đến trang about
@app.route("/about.html")
def about():
    return render_template("user/about.html")

# điều hướng đến trang contact 
@app.route("/contact.html")
def contact():
    return render_template("user/contact.html")

# điều hướng tới trang sự kiên (events) 
@app.route("/events.html")
def events():
    return render_template("user/events.html")

# điều hướng đên trang đặt chỗ (reservation)
@app.route("/reservation.html")
def reservation():
    return render_template("user/reservation.html")

# điều hướng tới trang phòng (rooms)
@app.route("/rooms.html")
def rooms():
    mydb=connect_to_database()
    mycursor=mydb.cursor()

    return render_template("user/rooms.html")

if __name__=="__main__":
    app.run(debug=True)


#Sử dụng strptime để chuyển đổi chuỗi ngày thành đối tượng datetime. 
#Sử dụng strftime để định dạng lại đối tượng datetime thành chuỗi mới với định dạng "%Y-%m-%d"