const cardDivs = document.querySelectorAll('.card');
const cardIds = [];

for (const cardDiv of cardDivs) {
  if (cardDiv.id) { // Check if the element has an id before accessing it
    cardIds.push(cardDiv.id);
  }
}

console.log(cardIds);