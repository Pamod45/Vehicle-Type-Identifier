function showPage(pageId) {
    // Hide all pages
    const pages = document.querySelectorAll('.page');
    pages.forEach(page => {
        page.classList.remove('active');
    });

    // Show the selected page
    const selectedPage = document.getElementById(pageId);
    selectedPage.classList.add('active');
}

//to upload the image to the home page
function homeUploadImage() {
    const fileInput = document.getElementById('file-input');
    fileInput.onchange = function() {
        homeDisplayImage(fileInput);
    };
    fileInput.click();
}

//to display the images in the home page
function homeDisplayImage(fileInput) {
    const imagePlaceHolder1 = document.getElementById('image-placeholder-1');
    const imagePlaceHolder2 = document.getElementById('image-placeholder-2');
    const files = fileInput.files;

    if (files.length > 0) {
        const formData = new FormData();
        formData.append('image', files[0]);

        fetch('/upload_home', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            
            const originalUrl = data.original_image_url;
            const timestamp = new Date().getTime();

            imagePlaceHolder1.style.backgroundImage = `url(${originalUrl}?t=${timestamp})`;
            imagePlaceHolder1.style.backgroundSize = 'cover'; 
            imagePlaceHolder1.style.backgroundPosition = 'center';
            const bottomMessage = document.getElementById('bottomMessage');
            
            if(data.message!="Please upload the backgorund image first"){
                const newUrl = data.new_image_url;

                imagePlaceHolder2.style.backgroundImage = `url(${newUrl}?t=${timestamp})`;
                imagePlaceHolder2.style.backgroundSize = 'cover'; 
                imagePlaceHolder2.style.backgroundPosition = 'center';
                if(data.get_probability){
                    if(data.identified_vehicle_type){
                    
                        let message = `This vehicle's Width: ${data.width}px, Height: ${data.height}px<br>`;
                        message += 'This vehicle is identified as a <span style="color: red; background-color:white; font-weight: bold;">'+data.vehicle_type+'</span><br>';

                        // Add probability details
                        message += `Vehicle being a car probability: ${data.vehicle_type === 'car' ? '<span style="color: red; background-color:white; font-weight: bold;">' + data.car_prob + '</span>' : data.car_prob}<br>`;
                        message += `Vehicle being a bus probability: ${data.vehicle_type === 'bus' ? '<span style="color: red; background-color:white; font-weight: bold;">' + data.bus_prob + '</span>' : data.bus_prob}<br>`;
                        message += `Vehicle being a bike probability: ${data.vehicle_type === 'bike' ? '<span style="color: red; background-color:white; font-weight: bold;">' + data.bike_prob + '</span>' : data.bike_prob}`;
                        
                        bottomMessage.innerHTML = message;
                        updateHistoryTable(data.vehicle_type, data.car_prob, data.bike_prob, data.bus_prob)
                    }
                    else{
                        bottomMessage.innerHTML = `Uploaded vehicle is not a identified vehicle type`;
                    }
                }
                else{
                    bottomMessage.innerHTML = `${data.message}`;
                }   
            }
            else{
                bottomMessage.innerHTML = `${data.message}`;
            }       
        })
        .catch(error => {
            console.error('Error:', error);
        });
    } else {
        console.log("No file selected");
    }
}
// to delete the images in the home page
function homeDeleteImage(){
    
    // Send a request to the server to delete the image file
    fetch('/delete_home_uploads', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const imagePlaceholder1 = document.getElementById('image-placeholder-1');
            const imagePlaceholder2 = document.getElementById('image-placeholder-2');
            const bottomMessage = document.getElementById('bottomMessage');

            imagePlaceholder1.style.backgroundImage = '';
            imagePlaceholder2.style.backgroundImage = '';

            bottomMessage.innerText = "Please upload an image";
        } else {
            console.error('Image deletion failed', data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

//to upload the images in the settings page
function settingUploadImage(placeholderId) {   
    const fileInput = document.getElementById('file-input-settings');
    fileInput.onchange = function() {
        settingDisplayImage(placeholderId, fileInput);
    };

    fileInput.click();
}

//to display the images in the settings page 
function settingDisplayImage(placeholder, fileInput) {
    const imagePlaceHolder = document.getElementById(placeholder);
    const files = fileInput.files;

    if (files.length > 0) {
        const formData = new FormData();
        formData.append('image', files[0]);
        formData.append('placeholder', placeholder);

        fetch('/upload_settings', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const imageUrl = data.url;
                const timestamp = new Date().getTime();
                imagePlaceHolder.style.backgroundImage = `url(${imageUrl}?t=${timestamp})`;
                imagePlaceHolder.style.backgroundSize = 'cover'; 
                imagePlaceHolder.style.backgroundPosition = 'center';
                
            } else {
                console.error('Image upload failed :',data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    } else {
        console.log("No file selected");
    }
}

//to delete the images in the settings page
function settingDeleteImage(placeholder) {
    var filename = '' ;
    if(placeholder == 'settings-placeholder-4')
        filename = 'background.jpg'
    else if(placeholder == 'settings-placeholder-1')
        filename = 'car.jpg'
    else if(placeholder == 'settings-placeholder-2')
        filename = 'bike.jpg'
    else if(placeholder == 'settings-placeholder-3')
        filename = 'bus.jpg'
    
    const imagePlaceHolder = document.getElementById(placeholder);
    
    // Send a request to the server to delete the image file
    fetch('/delete_settings', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ filename: filename })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            imagePlaceHolder.style.backgroundImage = 'none';
            if( filename =='background.jpg'){
                const imagePlaceHolder1 = document.getElementById('settings-placeholder-1');
                const imagePlaceHolder2 = document.getElementById('settings-placeholder-2');
                const imagePlaceHolder3 = document.getElementById('settings-placeholder-3');

                imagePlaceHolder1.style.backgroundImage = 'none';
                imagePlaceHolder2.style.backgroundImage = 'none';
                imagePlaceHolder3.style.backgroundImage = 'none';
            }
        } else {
            console.error('Image deletion failed');
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}


// to update the history table in the history table
function updateHistoryTable(vehicleType, car_prob, bike_prob, bus_prob) {
    const historyTable = document.getElementById('history-table').getElementsByTagName('tbody')[0];

    const currentDate = new Date();
    const date = currentDate.toISOString().split('T')[0]; 
    const time = currentDate.toTimeString().split(' ')[0]; 

    const newRow = historyTable.insertRow();
    const dateCell = newRow.insertCell(0);
    const timeCell = newRow.insertCell(1);
    const vehicleTypeCell = newRow.insertCell(2);
    const car_prob_cell = newRow.insertCell(3);
    const bike_prob_cell = newRow.insertCell(4);
    const bus_prob_cell = newRow.insertCell(5);

    // Set the cell text
    dateCell.innerText = date;
    timeCell.innerText = time;
    vehicleTypeCell.innerText = vehicleType;
    car_prob_cell.innerText = `${car_prob.toString().slice(0,5)}`
    bike_prob_cell.innerText = `${bike_prob.toString().slice(0,5)}`
    bus_prob_cell.innerText = `${bus_prob.toString().slice(0,5)}`   
    if (vehicleType === 'car') {
        car_prob_cell.style.color = 'red';
    } else if (vehicleType === 'bike') {
        bike_prob_cell.style.color = 'red';
    } else if (vehicleType === 'bus') {
        bus_prob_cell.style.color = 'red';
    }
    vehicleTypeCell.style.color = 'red';
    // Apply alternating row colors
    const rows = historyTable.getElementsByTagName('tr');
    for (let i = 0; i < rows.length; i++) {
        rows[i].style.backgroundColor = (i % 2 === 0) ? 'white' : 'lightgrey';
        
    }
}

// Show the home page by default
document.getElementById('home').classList.add('active');
