/* 
   Copyright (C) 2006 Jacek Sliwerski

   This program is free software; you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation; version 2.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program; if not, write to the Free Software Foundation,
   Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.  

   ----------------------------------------------------------------------

*/
/****************************************************************************
 *    IMPLEMENTATION HEADERS
 ****************************************************************************/

#include <stdlib.h>
#include <stdio.h>
#include <time.h>

#include "xmalloc.h"
#include "phrase.h"
#include "hash.h"
#include "storage.h"

/****************************************************************************
 *    IMPLEMENTATION PRIVATE DEFINITIONS / ENUMERATIONS / SIMPLE TYPEDEFS
 ****************************************************************************/
/****************************************************************************
 *    IMPLEMENTATION PRIVATE CLASS PROTOTYPES / EXTERNAL CLASS REFERENCES
 ****************************************************************************/
/****************************************************************************
 *    IMPLEMENTATION PRIVATE STRUCTURES / UTILITY CLASSES
 ****************************************************************************/
/****************************************************************************
 *    IMPLEMENTATION REQUIRED EXTERNAL REFERENCES (AVOID)
 ****************************************************************************/
/****************************************************************************
 *    IMPLEMENTATION PRIVATE DATA
 ****************************************************************************/
/****************************************************************************
 *    INTERFACE DATA
 ****************************************************************************/
/****************************************************************************
 *    IMPLEMENTATION PRIVATE FUNCTION PROTOTYPES
 ****************************************************************************/
/****************************************************************************
 *    IMPLEMENTATION PRIVATE FUNCTIONS
 ****************************************************************************/
/****************************************************************************
 *    INTERFACE FUNCTIONS
 ****************************************************************************/

static void
destroy_entry (void *key, void *value)
{
        phrase_destroy ((phrase_t *) key);
}


void
main_phrases (void)
{
        phrase_t *p1 = phrase_create ("ala");
        phrase_t *p2 = phrase_create ("ela");
        entry_t *entry;

        htable_t *table = htable_create_p (4);

        htable_insert (table, p1, p1);
        htable_insert (table, p2, p2);

        entry = htable_lookup (table, p2);

        phrase_print ((phrase_t *) entry->value);
        printf ("\n");

        htable_destroy (table, destroy_entry);
}


void
main_storage (void)
{
        int i;
        clock_t start;
        clock_t end;
        suggestion_t *sugg;
        
        storage_t *storage = storage_create ("C");

        start = clock ();
        storage_read (storage, "../data/fourth.db");
        end = clock ();

        printf ("time: %lf\n", ((double) (end - start)) / CLOCKS_PER_SEC);


        start = clock ();
        sugg = storage_suggest (storage, "couldn't convert %s to %s");
        end = clock ();

        printf ("time: %lf\n", ((double) (end - start)) / CLOCKS_PER_SEC);

        for (i = 0; i < sugg->count; i++){
                printf (" -> %d: %d\n", sugg->ids[i], sugg->values[i]);
        }

        xfree (sugg->ids);
        xfree (sugg->values);
        xfree (sugg);

        storage_destroy (storage);
}


void
main_bad_phrase (void)
{
        int i;
        
        phrase_t *phrase = phrase_create ("a b a");
        phrase_print (phrase);
        printf ("\n");
        printf ("%d, %d\n", phrase->word_count, phrase->length);

        for (i = 0; i < phrase->word_count; i++){
                phrase_print ((phrase_t *) phrase->words[i]);
                printf ("\n");
        }
}


int
main (int argc, char **argv)
{
        main_storage ();
        exit (EXIT_SUCCESS);
}

/****************************************************************************
 *
 *    END MODULE tran.c
 *
 ****************************************************************************/
