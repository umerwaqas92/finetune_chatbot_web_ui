

const chatButton = document.querySelector('.chatbox__button');
const chatContent = document.querySelector('.chatbox__support');

//"{{ url_for('static', filename='./assets/css/typing.css') }}
//{{ url_for('static', filename='./assets/css/typing.css') }
const icons = {
    isClicked: '<img src="/images/icons/chatbox-icon.svg" />',
    isNotClicked: '<img src="/images/icons/chatbox-icon.svg" />'
}


// Get elements
const messageInput = document.querySelector('.chatbox__footer input');
const chatMessages = document.querySelector('.chatbox__messages');


const inputField = document.querySelector('input[type="text"]');

inputField.addEventListener('keypress', (event) => {
  if (event.key === 'Enter') {
    sendButton.click();
  }
});


// Function to add message to chatbox
function addMessageToChatbox(message, className) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('messages__item', className);
    messageDiv.innerText = message;
    const chatMessages = document.querySelector('.chatbox__messages');
    chatMessages.insertBefore(messageDiv, chatMessages.firstChild);
  }

  function showTypingIndicator() {
    const typingIndicator = `
      <div class="messages__item messages__item--typing">
        <span class="messages__dot"></span>
        <span class="messages__dot"></span>
        <span class="messages__dot"></span>
      </div>
    `;
    // chatMessages.innerHTML += typingIndicator;
    chatMessages.insertAdjacentHTML('afterbegin', typingIndicator);

  }
  
  function removeTypingIndicator() {
    const typingIndicator = chatMessages.querySelector('.messages__item--typing');
    if (typingIndicator) {
      typingIndicator.remove();
    }
  }
  pre_add_message = "Hi im ai bot, how can i help you?!"
  addMessageToChatbox(pre_add_message, 'messages__item--visitor');
  
  

// Function to send message and receive response
function sendMessage() {
  // Get message from input field
  const message = messageInput.value;

  // Add message to chatbox

  
  addMessageToChatbox(message, 'messages__item--operator');

  // Clear input field
  messageInput.value = '';


  showTypingIndicator();
  

  fetch("http://127.0.0.1:5000/answer", {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        query: message
    })
  })
  .then(response => response.json())
  .then(data => {
    // Add response message to chatbox
    // console.log(data);
    const msg = data.response.replace(/[\r\n]+/gm, "\n").trim(); // remove blank lines

    removeTypingIndicator();

    addMessageToChatbox(msg, 'messages__item--visitor');
  })
  .catch(error => {
    addMessageToChatbox("Please try again", 'messages__item--visitor');
    // console.error(error);
  });
}

// Add event listener to send button
const sendButton = document.querySelector('.chatbox__footer .chatbox__send--footer');
sendButton.addEventListener('click', sendMessage);

const chatbox = new InteractiveChatbox(chatButton, chatContent, icons);
chatbox.display();
chatbox.toggleIcon(false, chatButton);


