const TAGS = ["funny", "heartfelt", "chaotic", "wisdom", "unhinged", "other"];
const TRUNCATE_LENGTH = 280;

let allComments = [];
let activeTag = null;
let searchTerm = "";

const grid = document.getElementById("grid");
const countEl = document.getElementById("count");
const emptyEl = document.getElementById("empty");
const searchInput = document.getElementById("search");
const tagFiltersEl = document.getElementById("tagFilters");
const shuffleBtn = document.getElementById("shuffle");

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function formatDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  if (isNaN(d)) return "";
  return d.toLocaleDateString(undefined, { year: "numeric", month: "short" });
}

function buildTagFilters() {
  const allBtn = document.createElement("button");
  allBtn.className = "tag-btn active";
  allBtn.textContent = "All";
  allBtn.dataset.tag = "";
  tagFiltersEl.appendChild(allBtn);

  TAGS.forEach((tag) => {
    const btn = document.createElement("button");
    btn.className = "tag-btn";
    btn.textContent = tag[0].toUpperCase() + tag.slice(1);
    btn.dataset.tag = tag;
    tagFiltersEl.appendChild(btn);
  });

  tagFiltersEl.addEventListener("click", (e) => {
    const btn = e.target.closest(".tag-btn");
    if (!btn) return;
    activeTag = btn.dataset.tag || null;
    [...tagFiltersEl.children].forEach((c) => c.classList.toggle("active", c === btn));
    render();
  });
}

function cardHtml(comment) {
  const isLong = comment.text.length > TRUNCATE_LENGTH;
  const shortText = isLong ? comment.text.slice(0, TRUNCATE_LENGTH).trim() + "…" : comment.text;

  return `
    <article class="card" data-id="${comment.id}">
      <span class="quote-mark" aria-hidden="true">&ldquo;</span>
      <div class="comment-text">
        <span class="short">${escapeHtml(shortText)}</span>
        ${isLong ? `<span class="full" hidden>${escapeHtml(comment.text)}</span>
        <button class="more-btn" type="button">Read more</button>` : ""}
      </div>
      <span class="tag-pill ${comment.tag || "other"}">${comment.tag || "other"}</span>
      <div class="meta">
        <span><span class="author">${escapeHtml(comment.author)}</span> · ${formatDate(comment.submittedAt)}</span>
        <a class="recipe-link" href="${escapeHtml(comment.recipeUrl)}" target="_blank" rel="noopener">
          ${escapeHtml(comment.recipeTitle)}
        </a>
      </div>
      <div class="meta">
        <span class="recommend-count">👍 ${comment.recommendedCount ?? 0} recommends</span>
      </div>
    </article>
  `;
}

function matchesSearch(comment, term) {
  if (!term) return true;
  const haystack = `${comment.text} ${comment.author} ${comment.recipeTitle}`.toLowerCase();
  return haystack.includes(term);
}

function render() {
  const term = searchTerm.trim().toLowerCase();
  const filtered = allComments.filter((c) => {
    const tagOk = !activeTag || (c.tag || "other") === activeTag;
    return tagOk && matchesSearch(c, term);
  });

  countEl.textContent = `${filtered.length} comment${filtered.length === 1 ? "" : "s"}`;
  emptyEl.hidden = filtered.length > 0;
  grid.innerHTML = filtered.map(cardHtml).join("");

  grid.querySelectorAll(".more-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const wrapper = btn.parentElement;
      const short = wrapper.querySelector(".short");
      const full = wrapper.querySelector(".full");
      short.hidden = true;
      full.hidden = false;
      btn.remove();
    });
  });
}

function shuffleToRandomCard() {
  if (allComments.length === 0) return;
  const random = allComments[Math.floor(Math.random() * allComments.length)];
  activeTag = null;
  searchTerm = "";
  searchInput.value = "";
  [...tagFiltersEl.children].forEach((c) => c.classList.toggle("active", c.dataset.tag === ""));
  render();
  requestAnimationFrame(() => {
    const card = grid.querySelector(`[data-id="${random.id}"]`);
    if (card) {
      card.scrollIntoView({ behavior: "smooth", block: "center" });
      card.style.outline = "2px solid var(--accent)";
      setTimeout(() => { card.style.outline = ""; }, 1200);
    }
  });
}

async function init() {
  buildTagFilters();

  searchInput.addEventListener("input", (e) => {
    searchTerm = e.target.value;
    render();
  });

  shuffleBtn.addEventListener("click", shuffleToRandomCard);

  try {
    const res = await fetch("data/published.json");
    allComments = await res.json();
  } catch (err) {
    countEl.textContent = "Couldn't load comments.";
    console.error(err);
    return;
  }

  // Newest / most-recommended first by default
  allComments.sort((a, b) => (b.recommendedCount ?? 0) - (a.recommendedCount ?? 0));
  render();
}

init();
