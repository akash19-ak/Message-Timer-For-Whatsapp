import React from 'react'

const TEMPLATES = [
  {
    id: 'funny',
    label: 'Funny',
    emoji: '😂',
    text: (name) =>
      `Happy Birthday ${name}! 🎂 Another year older, another year closer to needing GPS to find your keys. But hey, at least you're still fabulous! Have an epic day! 🥳🎉`,
  },
  {
    id: 'formal',
    label: 'Formal',
    emoji: '🎩',
    text: (name) =>
      `Dear ${name}, on the occasion of your birthday, I extend my warmest congratulations and heartfelt wishes. May this special day bring you joy, prosperity, and continued success in all your endeavors.`,
  },
  {
    id: 'friendly',
    label: 'Friendly',
    emoji: '🤗',
    text: (name) =>
      `Hey ${name}! 🎉 Happy Birthday! Wishing you an amazing day filled with laughter, love, and all your favorite things. Hope this year brings you everything you've been dreaming of! 🎂❤️`,
  },
  {
    id: 'sweet',
    label: 'Sweet',
    emoji: '🌸',
    text: (name) =>
      `Happy Birthday, ${name}! 🌸 On your special day, I want you to know how much you mean to me. You bring so much sunshine into the lives of everyone around you. Wishing you all the happiness in the world! 💕`,
  },
  {
    id: 'inspirational',
    label: 'Inspire',
    emoji: '🚀',
    text: (name) =>
      `Happy Birthday ${name}! 🚀 Another year of growth, resilience, and amazing achievements. Keep chasing your dreams with the same fire that makes you extraordinary. The world is better with you in it! ⭐`,
  },
  {
    id: 'party',
    label: 'Party',
    emoji: '🎊',
    text: (name) =>
      `HAPPY BIRTHDAY ${name.toUpperCase()}!!! 🎊🎉🥳 IT'S YOUR DAY TO PARTY HARD AND CELEBRATE! You deserve all the cake, confetti, and fun in the world! Let's gooo! 🎂🎈🍾`,
  },
]

export default function TemplateSelector({ name, onSelect, activeId, onActiveChange }) {
  const handleSelect = (template) => {
    onActiveChange(template.id)
    onSelect(template.text(name || 'Friend'))
  }

  return (
    <div className="form-group">
      <label className="form-label">🎨 Message Templates</label>
      <div className="template-grid">
        {TEMPLATES.map((t) => (
          <button
            key={t.id}
            type="button"
            className={`template-btn${activeId === t.id ? ' active' : ''}`}
            onClick={() => handleSelect(t)}
            title={`Use ${t.label} template`}
          >
            <span className="templ-emoji">{t.emoji}</span>
            {t.label}
          </button>
        ))}
      </div>
    </div>
  )
}
