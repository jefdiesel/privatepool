/**
 * Tests for Card component
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { Card, CardBack } from '@/components/poker/Card';

describe('Card', () => {
  describe('face up cards', () => {
    it('should render Ace of Hearts', () => {
      render(<Card card="Ah" />);

      expect(screen.getByText('A')).toBeInTheDocument();
      expect(screen.getByText('\u2665')).toBeInTheDocument(); // Heart symbol
    });

    it('should render King of Diamonds', () => {
      render(<Card card="Kd" />);

      expect(screen.getByText('K')).toBeInTheDocument();
      expect(screen.getByText('\u2666')).toBeInTheDocument(); // Diamond symbol
    });

    it('should render Queen of Clubs', () => {
      render(<Card card="Qc" />);

      expect(screen.getByText('Q')).toBeInTheDocument();
      expect(screen.getByText('\u2663')).toBeInTheDocument(); // Club symbol
    });

    it('should render Jack of Spades', () => {
      render(<Card card="Js" />);

      expect(screen.getByText('J')).toBeInTheDocument();
      expect(screen.getByText('\u2660')).toBeInTheDocument(); // Spade symbol
    });

    it('should render Ten correctly (T -> 10)', () => {
      render(<Card card="Th" />);

      expect(screen.getByText('10')).toBeInTheDocument();
    });

    it('should render number cards', () => {
      render(<Card card="7d" />);

      expect(screen.getByText('7')).toBeInTheDocument();
    });

    it('should render Two correctly', () => {
      render(<Card card="2s" />);

      expect(screen.getByText('2')).toBeInTheDocument();
    });
  });

  describe('face down cards', () => {
    it('should render face down card when faceDown is true', () => {
      const { container } = render(<Card card="Ah" faceDown />);

      // Should not show card value
      expect(screen.queryByText('A')).not.toBeInTheDocument();

      // Should have blue background (card back)
      const cardElement = container.firstChild as HTMLElement;
      expect(cardElement.className).toContain('bg-gradient-to-br');
      expect(cardElement.className).toContain('from-blue-800');
    });

    it('should render face down when card is empty string', () => {
      const { container } = render(<Card card="" />);

      const cardElement = container.firstChild as HTMLElement;
      expect(cardElement.className).toContain('bg-gradient-to-br');
    });
  });

  describe('sizes', () => {
    it('should render small size', () => {
      const { container } = render(<Card card="Ah" size="sm" />);

      const cardElement = container.firstChild as HTMLElement;
      expect(cardElement.className).toContain('w-8');
      expect(cardElement.className).toContain('h-12');
    });

    it('should render medium size (default)', () => {
      const { container } = render(<Card card="Ah" />);

      const cardElement = container.firstChild as HTMLElement;
      expect(cardElement.className).toContain('w-12');
      expect(cardElement.className).toContain('h-16');
    });

    it('should render large size', () => {
      const { container } = render(<Card card="Ah" size="lg" />);

      const cardElement = container.firstChild as HTMLElement;
      expect(cardElement.className).toContain('w-16');
    });
  });

  describe('colors', () => {
    it('should use red color for hearts', () => {
      const { container } = render(<Card card="Ah" />);

      // Find elements with red text color
      const redElements = container.querySelectorAll('.text-red-500');
      expect(redElements.length).toBeGreaterThan(0);
    });

    it('should use red color for diamonds', () => {
      const { container } = render(<Card card="Ad" />);

      const redElements = container.querySelectorAll('.text-red-500');
      expect(redElements.length).toBeGreaterThan(0);
    });

    it('should use black color for clubs', () => {
      const { container } = render(<Card card="Ac" />);

      const blackElements = container.querySelectorAll('.text-slate-900');
      expect(blackElements.length).toBeGreaterThan(0);
    });

    it('should use black color for spades', () => {
      const { container } = render(<Card card="As" />);

      const blackElements = container.querySelectorAll('.text-slate-900');
      expect(blackElements.length).toBeGreaterThan(0);
    });
  });

  describe('edge cases', () => {
    it('should handle uppercase suit', () => {
      render(<Card card="AH" />);

      expect(screen.getByText('A')).toBeInTheDocument();
      expect(screen.getByText('\u2665')).toBeInTheDocument();
    });

    it('should handle unknown rank gracefully', () => {
      render(<Card card="Xh" />);

      // Should render the raw rank if not in mapping
      expect(screen.getByText('X')).toBeInTheDocument();
    });
  });
});

describe('CardBack', () => {
  it('should render card back with default size', () => {
    const { container } = render(<CardBack />);

    const cardElement = container.firstChild as HTMLElement;
    expect(cardElement.className).toContain('w-12');
    expect(cardElement.className).toContain('h-16');
    expect(cardElement.className).toContain('bg-gradient-to-br');
  });

  it('should render card back with custom size', () => {
    const { container } = render(<CardBack size="lg" />);

    const cardElement = container.firstChild as HTMLElement;
    expect(cardElement.className).toContain('w-16');
  });
});
