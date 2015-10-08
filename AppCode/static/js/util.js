function displayMessage(){
	var message = document.getElementById("display_message");
	if(message) {
		if(message.value.length > 0) {
			alert(message.value);
		}
	}
}
