const unirest = require("unirest");
const cheerio = require("cheerio");

const getHTML = async(url) => {

    const response = await unirest.get(url);

    if(response.status == 200){
        return response.body
    }
}

const fetchPages = async (numPages, username) => {
  const promises = [];

  for (let i = 1; i <= numPages; i++) {
    promises.push(getHTML(`https://letterboxd.com/${username}/films/diary/page/${i}`));
  }

  return await Promise.all(promises);
};

const parseHTML = async () => {
  const username = "comrade_yui";
  const url = `https://letterboxd.com/${username}/`;
  const html = await getHTML(url);
  const $ = cheerio.load(html);

  const numberText = $(`a.all-link[href="/${username}/films/diary/"]`).text();
  const numberMoviesInDiary = parseInt(numberText.replace(/\D/g, ""));
  console.log(numberMoviesInDiary);

  const moviesPerPage = 50;
  const numPages = Math.ceil(numberMoviesInDiary / moviesPerPage);

  const filmSlugFrequency = {};

  const pageHtmls = await fetchPages(numPages, username);

  pageHtmls.forEach(pageHtml => {
    const $ = cheerio.load(pageHtml);

    $('tbody tr').each((index, element) => {
      const filmSlug = $(element).find('.td-film-details div[data-film-slug]').attr('data-film-slug');
      filmSlugFrequency[filmSlug] = (filmSlugFrequency[filmSlug] || 0) + 1;
    });
  });

  const filteredKeys = Object.keys(filmSlugFrequency).filter(key => filmSlugFrequency[key] > 1);
  filteredKeys.sort((a, b) => filmSlugFrequency[b] - filmSlugFrequency[a]);

  filteredKeys.forEach(key => {
    console.log(`${key}: ${filmSlugFrequency[key]}`);
  });
};

parseHTML();
