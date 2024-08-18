from flask import Flask, request, send_from_directory, render_template, jsonify, url_for
import cv2
import os
import numpy as np
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
SETTINGS_FOLDER = 'settings'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SETTINGS_FOLDER'] = SETTINGS_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER

car_width, car_height = 0, 0
bike_width, bike_height = 0, 0
bus_width, bus_height = 0, 0
uploaded_width, uploaded_height = 0, 0


# Create directories if they don't exist
for folder in [UPLOAD_FOLDER, SETTINGS_FOLDER, PROCESSED_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

#defining the route folder
@app.route('/')
def index():
    return render_template('index.html')

#to return file paths for the files in the static folder
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

#to return upload folder file paths for given file names
@app.route('/uploads/<filename>')
def serve_original(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

#to return processed folder file paths for given file names
@app.route('/processed/<filename>')
def serve_processed(filename):
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename)

#to return settings folder file paths for given file names
@app.route('/settings/<filename>')
def serve_settings(filename):
    return send_from_directory(app.config['SETTINGS_FOLDER'], filename)

#to upload the images to the upload folder
@app.route('/upload_home', methods=['POST'])
def upload_home_file():
    global uploaded_width, uploaded_height

    if 'image' not in request.files:
        return jsonify(success=False, message="No file part")
    
    file = request.files['image']
    if file.filename == '':
        return jsonify(success=False, message="No selected file")
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)

    #if file exists then delete the file first
    if os.path.exists(filepath):
        os.remove(filepath)

    #save the file to the uploads folder
    file.save(filepath)
    current_image = cv2.imread(filepath)
    original_upload_image = resize_image(current_image)
    cv2.imwrite(filepath, original_upload_image)
    original_image_url = url_for('serve_original', filename = file.filename)

    background_image_path = os.path.join(app.config['SETTINGS_FOLDER'], 'background.jpg')

    if os.path.exists(background_image_path):
        grey_background_image = cv2.cvtColor(cv2.imread(background_image_path), cv2.COLOR_BGR2GRAY)
        grey_source_uploaded_image = cv2.cvtColor(original_upload_image, cv2.COLOR_BGR2GRAY)
        vehicle_x, vehicle_y, uploaded_width, uploaded_height = find_contour_sizes(grey_source_uploaded_image, grey_background_image)
        detected_vehicle = draw_contours(original_upload_image, vehicle_x, vehicle_y, uploaded_width, uploaded_height)
        
        if uploaded_height > 450 and uploaded_width > 450 :
            return jsonify(success=False,original_image_url=original_image_url, message="Please upload image with similar background ")
        
        new_filename = 'new' + file.filename
        new_filepath = os.path.join(app.config['UPLOAD_FOLDER'], new_filename) 
        cv2.imwrite(new_filepath, detected_vehicle)
        
        new_image_url = url_for('serve_original', filename = new_filename)
        
        print('uploaded width: ' + str(uploaded_width) + ', uploaded height: ' + str(uploaded_height))
        if car_width==0 or car_height==0 or bike_width==0 or bike_height==0 or bus_width==0 or bus_height==0:
            return jsonify(success=True, original_image_url=original_image_url, new_image_url = new_image_url, get_probability=False,message="Settings images are missing.Please check and upload setting images first for detection.")
        else:
            car_prob, bike_prob, bus_prob = detecting_vehcile_type(uploaded_width,uploaded_height)
            detected_prob = max(car_prob, bike_prob, bus_prob)
            vehicle_type = ""
            if detected_prob == car_prob:
                vehicle_type = "car"
            elif detected_prob == bike_prob:
                vehicle_type = "bike"
            elif detected_prob == bus_prob:
                vehicle_type = "bus"

            identified_vehicle_type = False
            if detected_prob>40 :
                identified_vehicle_type = True

            return jsonify(success=True, original_image_url=original_image_url, new_image_url = new_image_url, 
                        car_prob=car_prob, bike_prob=bike_prob, bus_prob=bus_prob, identified_vehicle_type=identified_vehicle_type,
                        vehicle_type=vehicle_type,width = uploaded_width, height = uploaded_height,get_probability=True,message="probability calculated")

    return jsonify(success=False,original_image_url=original_image_url, message="Please upload the backgorund image first")

#to delete all the images in the upload folder
@app.route('/delete_home_uploads', methods=['POST'])
def delete_all_uploads_file():
    upload_folder = app.config['UPLOAD_FOLDER']

    try:
        # List all files in the upload folder
        files = os.listdir(upload_folder)
        
        # Remove each file
        for file in files:
            file_path = os.path.join(upload_folder, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
        
        return jsonify(success=True, message="All files deleted successfully.")
    except Exception as e:
        return jsonify(success=False, message=str(e))    


#to upload the settings images to the settings folder
@app.route('/upload_settings', methods=['POST'])
def upload_settings_file():
    global car_width, car_height, bike_width, bike_height, bus_width, bus_height
    if 'image' not in request.files:
        return jsonify(success=False, message="No file part")
    
    file = request.files['image']
    if file.filename == '':
        return jsonify(success=False, message="No selected file")

    placeholder = request.form['placeholder']
    if placeholder == 'settings-placeholder-4':
        filename = 'background.jpg'
    elif placeholder == 'settings-placeholder-1':
        filename = 'car.jpg'
    elif placeholder == 'settings-placeholder-2':
        filename = 'bike.jpg'
    elif placeholder == 'settings-placeholder-3':
        filename = 'bus.jpg'
    else:
        return jsonify(success=False, message="Invalid placeholder")
    
    filepath = os.path.join(app.config['SETTINGS_FOLDER'], filename)

    #if file exists then delete the file first
    if os.path.exists(filepath):
        os.remove(filepath)

    #save the file to the settings folder
    file.save(filepath)

    #saving the background image and exiting
    if filename == 'background.jpg' :
        current_image = cv2.imread(filepath)
        background_image = resize_image(current_image)
        cv2.imwrite(filepath, background_image)
        image_url = url_for('serve_settings', filename=filename)
        return jsonify(success=True, url=image_url)
    

    # Find contours and width and length of the vehicle in the image 
    background_image_path = os.path.join(app.config['SETTINGS_FOLDER'], 'background.jpg')
    current_image = cv2.imread(filepath)
    original_vehicle_image = resize_image(current_image)

    if os.path.exists(background_image_path):
        grey_background_image = cv2.cvtColor(cv2.imread(background_image_path), cv2.COLOR_BGR2GRAY)
        grey_source_vehicle_image = cv2.cvtColor(original_vehicle_image, cv2.COLOR_BGR2GRAY)
        vehicle_x, vehicle_y, vehicle_width, vehicle_height = find_contour_sizes(grey_source_vehicle_image, grey_background_image)
        detected_vehicle = draw_contours(original_vehicle_image, vehicle_x, vehicle_y, vehicle_width, vehicle_height)
        cv2.imwrite(filepath, detected_vehicle)
        image_url = url_for('serve_settings', filename=filename)

        if filename=='car.jpg':
            car_width = vehicle_width
            car_height = vehicle_height
        elif filename=='bike.jpg':
            bike_width = vehicle_width
            bike_height = vehicle_height
        elif filename == 'bus.jpg':
            bus_width = vehicle_width
            bus_height = vehicle_height
        print('Car width: ' + str(car_width) + ', Car height: ' + str(car_height) + '\n' +
                'Bike width: ' + str(bike_width) + ', Bike height: ' + str(bike_height) + '\n' +
                'Bus width: ' + str(bus_width) + ', Bus height: ' + str(bus_height))

        return jsonify(success=True, url=image_url)
        
    return jsonify(success=False, message="Please upload the backgorund image first")

#to delete the images in the settings folder
@app.route('/delete_settings', methods=['POST'])
def delete_settings_file():
    global car_height, car_width, bike_height, bike_width, bus_height, bus_width
    data = request.get_json()
    filename = data.get('filename')
    print(filename)
    if not filename:
        return jsonify(success=False, message="Filename not provided"), 400

    filepath = os.path.join(app.config['SETTINGS_FOLDER'], filename)
    
    if os.path.exists(filepath):
        if filename == 'background.jpg' :
            source_car = os.path.join(app.config['SETTINGS_FOLDER'], 'car.jpg')
            source_bike = os.path.join(app.config['SETTINGS_FOLDER'], 'bike.jpg')
            source_bus = os.path.join(app.config['SETTINGS_FOLDER'], 'bus.jpg')
            if os.path.exists(source_car):
                os.remove(source_car)
            if os.path.exists(source_bike):
                os.remove(source_bike)
            if os.path.exists(source_bus):
                os.remove(source_bus)
            car_height=0
            car_width=0
            bike_height=0
            bike_width=0
            bus_height=0
            bus_width=0

        os.remove(filepath)
        if filename=='bike.jpg':
            bike_height=0
            bike_width=0
        elif filename == 'car.jpg':
            car_height=0
            car_width=0
        elif filename== 'bus.jpg':
            bus_height=0
            bus_width=0
        return jsonify(success=True, message="File deleted")
    else:
        return jsonify(success=False, message="File not found"), 404
    

## image processing functions 

#resize the image to given size
def resize_image(image, size=(500, 500)):
  resized_img = cv2.resize(image, size, interpolation=cv2.INTER_AREA)
  return resized_img

#dilate the image
def apply_dilation(image):
    reduced_percentage = 0
    black_pixels = np.sum(image == 0)
    if black_pixels == 0:
      return image
    i = 0
    while reduced_percentage < 5:
      i = i + 1
      kernel = np.ones((i, i), np.uint8)  # Structuring element
      dilated_image = cv2.dilate(image, kernel, iterations=1)
      black_pixels_after = np.sum(dilated_image == 0)
      reduced_percentage = (black_pixels - black_pixels_after) / black_pixels * 100
    return dilated_image

#segment the object
def segment_objects(image,background_image):
  kernal_size = 5
  image = cv2.GaussianBlur(image, (kernal_size, kernal_size), 0)
  background_image = cv2.GaussianBlur(background_image, (kernal_size, kernal_size), 0)
  mask = np.zeros_like(image)

  rows, cols = image.shape
  for i in range(rows):
    for j in range(cols):
        if np.abs(int(background_image[i, j]) - int(image[i, j])) > 15:
            mask[i, j] = 255
        else:
            mask[i, j] = 0
  dilated_mask = apply_dilation(mask)
  segmented_vehicle = cv2.bitwise_and(image, dilated_mask, mask=dilated_mask)
  return segmented_vehicle, mask

#find the largest contour present in the image and written its attributes
def find_contour_sizes(image,background_iamge):
  segmented_image,mask = segment_objects(image,background_iamge)
  contours, _ = cv2.findContours(segmented_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

  if contours:
      largest_contour = max(contours, key=cv2.contourArea)
      x, y, w, h = cv2.boundingRect(largest_contour)
      return x,y,w,h
  else:
      return None
  
#finally draw contours
def draw_contours(image, x, y, width, height):
    annotated_image = image.copy()
    cv2.rectangle(annotated_image, (x, y), (x + width, y + height), (0, 255, 0), 2)
    text = f'W: {width} px, H: {height} px'

    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    text_color = (255, 0, 0)
    bg_color = (255, 255, 255)
    thickness = 2

    text_size, baseline = cv2.getTextSize(text, font, font_scale, thickness)

    text_x = x
    text_y = y - 10 if y - 10 > 10 else y + text_size[1] + 10

    cv2.rectangle(annotated_image,
                  (text_x, text_y - text_size[1] - baseline),
                  (text_x + text_size[0], text_y + baseline),
                  bg_color,
                  thickness=cv2.FILLED)
    cv2.putText(annotated_image, text, (text_x, text_y), font, font_scale, text_color, thickness)
    return annotated_image

def detecting_vehcile_type(detected_width, detected_height):
  detected_ratio = detected_height/detected_width
  source_car_ratio = car_height/car_width
  source_bike_ratio = bike_height/bike_width
  source_bus_ratio = bus_height/bus_width

  car_diff = abs(detected_ratio - source_car_ratio) / source_car_ratio
  bike_diff = abs(detected_ratio - source_bike_ratio) / source_bike_ratio
  bus_diff = abs(detected_ratio - source_bus_ratio) / source_bus_ratio

  car_prob = max(0, 1 - car_diff) * 100
  bike_prob = max(0, 1 - bike_diff) * 100
  bus_prob = max(0, 1 - bus_diff) * 100

  print("Being a car probability :", car_prob, "%")
  print("Being a bike probability :", bike_prob, "%")
  print("Being a bus probability :", bus_prob, "%")
  
  return car_prob, bike_prob, bus_prob

if __name__ == '__main__':
    app.run(debug=True)
